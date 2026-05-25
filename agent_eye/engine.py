import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os

class ImageCompareEngine:
    def __init__(self, threshold=30, dilation_size=None, min_area=None, merge_dist=None, auto_layout=False):
        """
        Initialize the Image Compare Engine.
        
        Args:
            threshold (int): Pixels in diff mask with values above this threshold (0-255) 
                             are considered significantly different. Default is 30 (~12% difference).
            dilation_size (int, optional): Size of the kernel used to dilate the difference mask. 
                                           If None, dynamically computed based on logical width.
            min_area (int, optional): Minimum pixel area of a bounding box to be reported. 
                                      If None, dynamically computed based on logical width.
            merge_dist (int, optional): Maximum distance in pixels between two bounding boxes to merge them.
                                        If None, dynamically computed based on logical width.
            auto_layout (bool): Enable horizontal-gap-based vertical segmented layout alignment.
        """
        self.threshold = threshold
        self._input_dilation_size = dilation_size
        self._input_min_area = min_area
        self._input_merge_dist = merge_dist
        self.auto_layout = auto_layout
        
        # Computed dynamically in compare()
        self.dilation_size = dilation_size
        self.min_area = min_area
        self.merge_dist = merge_dist

    def segment_and_align(self, img1, img2, search_window=60, correlation_threshold=0.55):
        """
        Segment img1 based on horizontal white gaps and locally align each segment
        with img2 using 1D template matching.
        
        Args:
            img1 (numpy.ndarray): Mockup/Design image (BGR).
            img2 (numpy.ndarray): Screenshot image (BGR, width-aligned).
            search_window (int): Vertical search range in pixels (±window).
            correlation_threshold (float): Minimum correlation score to consider alignment valid.
            
        Returns:
            tuple: (img1, aligned_img2) as BGR numpy arrays.
        """
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # Ensure img2 is first resized to the same width as img1 to allow strip matching
        if w1 != w2:
            scale = w1 / w2
            img2 = cv2.resize(img2, (w1, int(h2 * scale)), interpolation=cv2.INTER_AREA)
            h2, w2 = img2.shape[:2]
            
        # Grayscale representation for projection
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        
        # We consider a row to be a white gap if > 99% of its pixels are close to white (>250)
        row_non_white = np.sum(gray1 < 250, axis=1)
        content_signal = (row_non_white > (w1 * 0.01)).astype(np.uint8)
        
        # Find visual content bands
        bands = []
        in_band = False
        start_y = 0
        for y in range(h1):
            if content_signal[y] == 1 and not in_band:
                start_y = y
                in_band = True
            elif content_signal[y] == 0 and in_band:
                end_y = y
                bands.append([start_y, end_y])
                in_band = False
        if in_band:
            bands.append([start_y, h1])
            
        # Merge close bands (gap < 15px)
        merged_bands = []
        for band in bands:
            if not merged_bands:
                merged_bands.append(band)
            else:
                last_band = merged_bands[-1]
                gap = band[0] - last_band[1]
                if gap < 15:
                    last_band[1] = band[1]
                else:
                    merged_bands.append(band)
                    
        # Filter thin bands (< 8px height)
        final_bands = [b for b in merged_bands if (b[1] - b[0]) >= 8]
        print(f"Layout Engine: Segmented design into {len(final_bands)} visual component bands.")
        
        # Initialize aligned image matching img1's size
        aligned_img2 = np.ones((h1, w1, 3), dtype=np.uint8) * 255
        
        for i, (start_y, end_y) in enumerate(final_bands):
            strip = img1[start_y:end_y, :]
            strip_h = end_y - start_y
            
            # Local 1D search window in img2
            search_min_y = max(0, start_y - search_window)
            search_max_y = min(h2, end_y + search_window)
            
            # Template matching requires search area height > template height
            if (search_max_y - search_min_y) <= strip_h:
                shift = 0
            else:
                search_area = img2[search_min_y:search_max_y, :]
                res = cv2.matchTemplate(search_area, strip, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                
                if max_val >= correlation_threshold:
                    best_y = search_min_y + max_loc[1]
                    shift = best_y - start_y
                    print(f"  - Component Band #{i+1} (y={start_y}..{end_y}): aligned successfully, vertical shift {shift:+d}px (correlation: {max_val*100:.1f}%)")
                else:
                    shift = 0
                    
            # Copy shifted band
            src_y1 = start_y + shift
            src_y2 = end_y + shift
            src_y1_clamp = max(0, min(src_y1, h2))
            src_y2_clamp = max(0, min(src_y2, h2))
            copy_h = src_y2_clamp - src_y1_clamp
            
            if copy_h > 0:
                aligned_img2[start_y:start_y + copy_h, :] = img2[src_y1_clamp:src_y2_clamp, :]
                
        return img1, aligned_img2

    def load_and_align_images(self, path1, path2, method="pad"):
        """
        Load two images and align their dimensions so they can be compared.
        Supports DPI normalization and segmented vertical alignment.
        
        Args:
            path1 (str): Path to image 1 (e.g., Mockup/Design).
            path2 (str): Path to image 2 (e.g., Screenshot).
            method (str): "pad" to pad with white pixels, "resize" to stretch image 2 to match image 1.
            
        Returns:
            tuple: (img1_aligned, img2_aligned) as BGR numpy arrays.
        """
        if not os.path.exists(path1):
            raise FileNotFoundError(f"Image 1 not found: {path1}")
        if not os.path.exists(path2):
            raise FileNotFoundError(f"Image 2 not found: {path2}")

        img1 = cv2.imread(path1)
        img2 = cv2.imread(path2)

        if img1 is None:
            raise ValueError(f"Failed to read Image 1: {path1}")
        if img2 is None:
            raise ValueError(f"Failed to read Image 2: {path2}")

        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]

        # 1. Auto DPI Normalization
        ratio = w2 / w1
        dpr = round(ratio)
        if dpr >= 2 and abs(ratio - dpr) < 0.25:
            new_w2 = w1
            new_h2 = int(h2 / dpr)
            img2 = cv2.resize(img2, (new_w2, new_h2), interpolation=cv2.INTER_AREA)
            h2, w2 = img2.shape[:2]
            print(f"Smart DPI normalization: scaled Screenshot down {dpr}x to {w2}x{h2}")

        # 2. Segmented Layout Alignment
        if self.auto_layout:
            img1_aligned, img2_aligned = self.segment_and_align(img1, img2)
            return img1_aligned, img2_aligned

        # 3. Naive Dimensions Alignment
        if (h1, w1) == (h2, w2):
            return img1, img2

        if method == "resize":
            # Stretch/shrink img2 to match img1
            img2_aligned = cv2.resize(img2, (w1, h1), interpolation=cv2.INTER_AREA if (h2 > h1 or w2 > w1) else cv2.INTER_CUBIC)
            return img1, img2_aligned
            
        elif method == "pad":
            # Pad both to the max height and max width using white background (common for UI)
            max_h = max(h1, h2)
            max_w = max(w1, w2)

            img1_aligned = np.ones((max_h, max_w, 3), dtype=np.uint8) * 255
            img2_aligned = np.ones((max_h, max_w, 3), dtype=np.uint8) * 255

            img1_aligned[0:h1, 0:w1] = img1
            img2_aligned[0:h2, 0:w2] = img2

            return img1_aligned, img2_aligned
        else:
            raise ValueError(f"Unknown alignment method: {method}")

    def _merge_boxes(self, boxes):
        """
        Merge overlapping or closely adjacent bounding boxes.
        
        Args:
            boxes (list): List of tuple (x, y, w, h)
            
        Returns:
            list: List of merged tuple (x, y, w, h)
        """
        if not boxes:
            return []

        # Convert to [x1, y1, x2, y2]
        coords = []
        for x, y, w, h in boxes:
            coords.append([x, y, x + w, y + h])

        merged = []
        while coords:
            curr = coords.pop(0)
            has_merged = False
            for i, other in enumerate(merged):
                # Check distance/overlap between curr and other
                # Expand box by self.merge_dist to see if they overlap
                ox1, oy1, ox2, oy2 = other
                cx1, cy1, cx2, cy2 = curr
                
                # Check overlap of expanded boxes
                if not (cx2 + self.merge_dist < ox1 or
                        cx1 - self.merge_dist > ox2 or
                        cy2 + self.merge_dist < oy1 or
                        cy1 - self.merge_dist > oy2):
                    # Merge them
                    merged[i] = [
                        min(ox1, cx1),
                        min(oy1, cy1),
                        max(ox2, cx2),
                        max(oy2, cy2)
                    ]
                    has_merged = True
                    break
            
            if not has_merged:
                # Also check against remaining coordinates in the queue
                j = 0
                while j < len(coords):
                    other = coords[j]
                    cx1, cy1, cx2, cy2 = curr
                    ox1, oy1, ox2, oy2 = other
                    
                    if not (cx2 + self.merge_dist < ox1 or
                            cx1 - self.merge_dist > ox2 or
                            cy2 + self.merge_dist < oy1 or
                            cy1 - self.merge_dist > oy2):
                        # Merge other into curr and remove other from list
                        curr = [
                            min(ox1, cx1),
                            min(oy1, cy1),
                            max(ox2, cx2),
                            max(oy2, cy2)
                        ]
                        coords.pop(j)
                    else:
                        j += 1
                merged.append(curr)

        # Convert back to (x, y, w, h)
        return [(x1, y1, x2 - x1, y2 - y1) for x1, y1, x2, y2 in merged]

    def _find_best_uvt_match(self, box, uvt_node):
        """
        Recursively traverse the UVT JSON tree and find the deepest child node
        whose bounding box significantly overlaps with the given visual difference box.
        
        Args:
            box (list): [x, y, w, h] of the visual mismatch region.
            uvt_node (dict): Current UVT node.
            
        Returns:
            dict: The best matching node (or None if no match).
        """
        if not uvt_node or "box" not in uvt_node:
            return None

        nx, ny, nw, nh = uvt_node["box"]
        bx, by, bw, bh = box

        # Calculate intersection area
        x1 = max(nx, bx)
        y1 = max(ny, by)
        x2 = min(nx + nw, bx + bw)
        y2 = min(ny + nh, by + bh)

        inter_w = max(0, x2 - x1)
        inter_h = max(0, y2 - y1)
        inter_area = inter_w * inter_h

        if inter_area == 0:
            return None

        # Check children recursively to find the deepest/most-specific match
        if "children" in uvt_node and isinstance(uvt_node["children"], list):
            for child in uvt_node["children"]:
                match = self._find_best_uvt_match(box, child)
                if match:
                    # Deeper child match found and preferred
                    return match

        # If no child matches or this node is a leaf, this node is the best match
        return uvt_node

    def compare(self, path1, path2, align_method="pad", uvt=None, focus_mode="full"):
        """
        Compare two images and return a detailed discrepancy analysis.
        Supports semantic mapping using Unified View Tree (UVT) and Visual Attention Focus Modes.
        
        Args:
            path1 (str): Path to image 1 (Mockup).
            path2 (str): Path to image 2 (Screenshot).
            align_method (str): Method for image alignment ("pad" or "resize").
            uvt (dict, optional): Unified View Tree dictionary for semantic mapping.
            focus_mode (str): Visual Attention Mode: "full", "structure", "details", or "style".
            
        Returns:
            dict: Analysis results containing similarity metrics, discrepancy regions, and diff images.
        """
        # 1. Load and align
        img1, img2 = self.load_and_align_images(path1, path2, method=align_method)
        width = img1.shape[1]

        # 2. Preprocess images and compute focus-mode-specific thresholds
        if focus_mode == "structure":
            # Coarse-Grained Structural Focus: Apply a strong Gaussian blur to melt away text/icons
            blur1 = cv2.GaussianBlur(img1, (17, 17), 0)
            blur2 = cv2.GaussianBlur(img2, (17, 17), 0)
            gray1 = cv2.cvtColor(blur1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(blur2, cv2.COLOR_BGR2GRAY)
            
            # Widen parameters to capture large layout block elements
            dilation = self._input_dilation_size if self._input_dilation_size is not None else max(8, int(width * 0.025))
            min_area = self._input_min_area if self._input_min_area is not None else max(50, int(width * width * 0.0004))
            merge = self._input_merge_dist if self._input_merge_dist is not None else max(10, int(width * 0.03))
            
        elif focus_mode == "details":
            # Fine-Grained Text Focus: Use Laplacian to extract high-frequency text edges and neutralize backgrounds
            gray1_raw = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2_raw = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            gray1_lap = cv2.Laplacian(gray1_raw, cv2.CV_64F)
            gray2_lap = cv2.Laplacian(gray2_raw, cv2.CV_64F)
            
            gray1 = cv2.convertScaleAbs(gray1_lap)
            gray2 = cv2.convertScaleAbs(gray2_lap)
            
            # Tight parameters to isolate tiny local characters/lines
            dilation = self._input_dilation_size if self._input_dilation_size is not None else max(2, int(width * 0.005))
            min_area = self._input_min_area if self._input_min_area is not None else max(5, int(width * width * 0.00005))
            merge = self._input_merge_dist if self._input_merge_dist is not None else max(3, int(width * 0.008))
            
        elif focus_mode == "style":
            # Color Theme Focus: heavy blur on HSV representation to analyze broad colors while neutralizing layout shift
            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
            
            # Smooth HSV to remove edges
            blur1 = cv2.GaussianBlur(hsv1, (15, 15), 0)
            blur2 = cv2.GaussianBlur(hsv2, (15, 15), 0)
            
            # Use saturation and value channels or direct BGR absolute smoothed diff
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            gray1 = cv2.GaussianBlur(gray1, (11, 11), 0)
            gray2 = cv2.GaussianBlur(gray2, (11, 11), 0)
            
            dilation = self._input_dilation_size if self._input_dilation_size is not None else max(5, int(width * 0.015))
            min_area = self._input_min_area if self._input_min_area is not None else max(20, int(width * width * 0.0002))
            merge = self._input_merge_dist if self._input_merge_dist is not None else max(8, int(width * 0.02))
            
        else: # "full" / standard
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Dynamic scale-independent parameters
            dilation = self._input_dilation_size if self._input_dilation_size is not None else max(3, int(width * 0.015))
            min_area = self._input_min_area if self._input_min_area is not None else max(10, int(width * width * 0.0001))
            merge = self._input_merge_dist if self._input_merge_dist is not None else max(4, int(width * 0.02))

        self.dilation_size = dilation
        self.min_area = min_area
        self.merge_dist = merge

        # 3. Calculate Structural Similarity Index (SSIM)
        score, diff_map = ssim(gray1, gray2, full=True)

        # 4. Process Difference Map
        # Convert diff_map from [-1, 1] to a [0, 255] uint8 discrepancy mask
        diff_mask = (1.0 - diff_map) / 2.0  # normalized to [0, 1]
        diff_mask = (diff_mask * 255).astype(np.uint8)

        # 5. Threshold and Morphological Dilation
        _, thresh = cv2.threshold(diff_mask, self.threshold, 255, cv2.THRESH_BINARY)
        
        # Dilation to group close pixels together
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (self.dilation_size, self.dilation_size))
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        # 6. Find Contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get initial bounding boxes
        raw_boxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h >= self.min_area:
                raw_boxes.append((x, y, w, h))

        # 7. Merge overlapping or closely adjacent boxes
        merged_boxes = self._merge_boxes(raw_boxes)

        # 8. Analyze each region
        regions = []
        total_pixels = img1.shape[0] * img1.shape[1]
        mismatched_pixels = cv2.countNonZero(thresh)
        mismatch_percentage = (mismatched_pixels / total_pixels) * 100.0

        for idx, (x, y, w, h) in enumerate(merged_boxes):
            # Crop local regions to calculate specific regional scores
            crop_mask = thresh[y:y+h, x:x+w]
            crop_img1 = img1[y:y+h, x:x+w]
            crop_img2 = img2[y:y+h, x:x+w]

            # Mismatch ratio: ratio of different pixels inside this bounding box
            local_mismatched_pixels = cv2.countNonZero(crop_mask)
            mismatch_ratio = local_mismatched_pixels / (w * h)

            # Mean color difference (MAE in BGR space)
            abs_diff = cv2.absdiff(crop_img1, crop_img2)
            mean_color_diff = float(np.mean(abs_diff))

            # Severity classification
            if mismatch_ratio > 0.4 or mean_color_diff > 60:
                severity = "Critical"
            elif mismatch_ratio > 0.15 or mean_color_diff > 25:
                severity = "Warning"
            else:
                severity = "Info"

            region_data = {
                "id": idx + 1,
                "box": [int(x), int(y), int(w), int(h)],
                "mismatch_ratio": float(mismatch_ratio),
                "mean_color_diff": mean_color_diff,
                "severity": severity
            }

            # Map to DOM selector if UVT is provided
            if uvt:
                best_node = self._find_best_uvt_match([int(x), int(y), int(w), int(h)], uvt)
                if best_node:
                    region_data["selector"] = best_node.get("selector", "")
                    region_data["element_type"] = best_node.get("type", "")

            regions.append(region_data)

        # Sort regions by severity (Critical first) and then by size
        severity_order = {"Critical": 0, "Warning": 1, "Info": 2}
        regions.sort(key=lambda r: (severity_order[r["severity"]], -r["box"][2] * r["box"][3]))

        return {
            "overall_similarity": float(score),
            "overall_mismatch_percentage": float(mismatch_percentage),
            "regions": regions,
            "img1_aligned": img1,
            "img2_aligned": img2,
            "diff_mask": diff_mask,
            "thresh_mask": thresh
        }
