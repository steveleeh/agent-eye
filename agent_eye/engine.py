import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os

class ImageCompareEngine:
    def __init__(self, threshold=30, dilation_size=15, min_area=50, merge_dist=15):
        """
        Initialize the Image Compare Engine.
        
        Args:
            threshold (int): Pixels in diff mask with values above this threshold (0-255) 
                             are considered significantly different. Default is 30 (~12% difference).
            dilation_size (int): Size of the kernel used to dilate the difference mask. 
                                 Larger values merge nearby differences. Default is 15.
            min_area (int): Minimum pixel area of a bounding box to be reported. 
                            Used to filter out tiny noise (e.g. anti-aliasing artifacts). Default is 50.
            merge_dist (int): Maximum distance in pixels between two bounding boxes to merge them.
                              Default is 15.
        """
        self.threshold = threshold
        self.dilation_size = dilation_size
        self.min_area = min_area
        self.merge_dist = merge_dist

    def load_and_align_images(self, path1, path2, method="pad"):
        """
        Load two images and align their dimensions so they can be compared.
        
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

    def compare(self, path1, path2, align_method="pad"):
        """
        Compare two images and return a detailed discrepancy analysis.
        
        Args:
            path1 (str): Path to image 1 (Mockup).
            path2 (str): Path to image 2 (Screenshot).
            align_method (str): Method for image alignment ("pad" or "resize").
            
        Returns:
            dict: Analysis results containing similarity metrics, discrepancy regions, and diff images.
        """
        # 1. Load and align
        img1, img2 = self.load_and_align_images(path1, path2, method=align_method)
        
        # 2. Convert to Grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # 3. Calculate Structural Similarity Index (SSIM)
        # Note: skimage ssim expects grayscale, returns (score, full_diff_map)
        # ssim score is in [-1, 1], diff_map is in [-1, 1] (1 means identical)
        score, diff_map = ssim(gray1, gray2, full=True)

        # 4. Process Difference Map
        # Convert diff_map from [-1, 1] to a [0, 255] uint8 discrepancy mask
        # Where 0 = identical (diff_map=1.0) and 255 = maximum discrepancy (diff_map=-1.0)
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

            regions.append({
                "id": idx + 1,
                "box": [int(x), int(y), int(w), int(h)],
                "mismatch_ratio": float(mismatch_ratio),
                "mean_color_diff": mean_color_diff,
                "severity": severity
            })

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
