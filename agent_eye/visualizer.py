import cv2
import numpy as np

class ImageCompareVisualizer:
    @staticmethod
    def draw_annotated_image(img, regions, thresh_mask=None, tint_weight=0.25):
        """
        Draw color-coded bounding boxes and optional transparent red tints on mismatched areas.
        
        Args:
            img (numpy array): The image to annotate (typically the aligned screenshot).
            regions (list): The list of regions from the compare engine.
            thresh_mask (numpy array, optional): Binary difference mask to apply red tint to.
            tint_weight (float): Alpha transparency weight for the red mismatch tint.
            
        Returns:
            numpy array: Annotated image.
        """
        annotated = img.copy()
        h, w = annotated.shape[:2]

        # 1. Apply visual red tint to different pixels if threshold mask is provided
        if thresh_mask is not None:
            # Create a solid red overlay
            red_overlay = np.zeros_like(annotated)
            red_overlay[:, :] = [0, 0, 255]  # Red in BGR

            # Mask of different pixels
            mask = thresh_mask > 0
            
            # Blend the red overlay with the original image only at the mask pixels
            blended = cv2.addWeighted(annotated, 1.0 - tint_weight, red_overlay, tint_weight, 0)
            annotated[mask] = blended[mask]

        # Colors mapped in BGR
        severity_colors = {
            "Critical": (0, 0, 255),       # Red
            "Warning": (0, 140, 255),     # Orange
            "Info": (0, 255, 255)         # Yellow
        }

        # 2. Draw bounding boxes and text badges
        for reg in regions:
            x, y, rw, rh = reg["box"]
            severity = reg["severity"]
            color = severity_colors.get(severity, (255, 0, 0))
            
            # Bounding box outline
            cv2.rectangle(annotated, (x, y), (x + rw, y + rh), color, 2)

            # Draw small background box for text badge
            pct = int(reg["mismatch_ratio"] * 100)
            badge_text = f"#{reg['id']} {severity} ({pct}%)"
            
            # Get text dimensions
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.4
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(badge_text, font, font_scale, thickness)
            
            # Badge position (draw on top of box, shift inside if at image top boundary)
            badge_y1 = max(0, y - text_h - 6)
            badge_y2 = y
            if y < text_h + 8:
                # If too close to the top, draw badge inside the box
                badge_y1 = y
                badge_y2 = y + text_h + 6
            
            badge_x1 = x
            badge_x2 = min(w, x + text_w + 10)

            # Draw solid badge background
            cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), color, -1)
            
            # Draw badge text (white text or dark text depending on severity readability)
            text_color = (255, 255, 255) if severity != "Info" else (0, 0, 0)
            text_y = badge_y2 - 3 if badge_y1 == y - text_h - 6 else badge_y2 - 3
            cv2.putText(annotated, badge_text, (badge_x1 + 5, text_y), font, font_scale, text_color, thickness, cv2.LINE_AA)

        return annotated

    @staticmethod
    def create_comparison_panel(img1, img2_annotated, diff_mask):
        """
        Create a beautiful, professional side-by-side comparison dashboard containing:
        [1. Design Mockup] [2. Aligned Screenshot with Diff Overlay] [3. Visual Diff Heatmap]
        
        Args:
            img1 (numpy array): Aligned design mockup.
            img2_annotated (numpy array): Aligned and annotated screenshot.
            diff_mask (numpy array): Grayscale difference mask (0-255).
            
        Returns:
            numpy array: Single combined dashboard image.
        """
        h, w = img1.shape[:2]
        
        # 1. Create a beautiful colormap heatmap for the diff mask
        # 0 in diff_mask means identical, 255 means different.
        # We want identical to look dark-blue, and differences to look red-hot.
        # cv2.applyColorMap needs a uint8 image
        heatmap = cv2.applyColorMap(diff_mask, cv2.COLORMAP_JET)

        # 2. Add headers above each image
        header_h = 50
        panel_w = w
        
        # Create a header canvas
        def make_panel_with_header(img, title):
            canvas = np.ones((h + header_h, panel_w, 3), dtype=np.uint8) * 30  # Dark theme header background
            # Draw title text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (tw, th), _ = cv2.getTextSize(title, font, font_scale, thickness)
            
            # Center title text in the header bar
            text_x = (panel_w - tw) // 2
            text_y = (header_h + th) // 2
            
            cv2.putText(canvas, title, (text_x, text_y), font, font_scale, (200, 200, 200), thickness, cv2.LINE_AA)
            
            # Put the image below the header
            canvas[header_h:, :] = img
            return canvas

        panel1 = make_panel_with_header(img1, "1. ORIGINAL DESIGN MOCKUP")
        panel2 = make_panel_with_header(img2_annotated, "2. SCREENSHOT (ANNOTATED)")
        panel3 = make_panel_with_header(heatmap, "3. STRUCTURAL DIFF HEATMAP")

        # 3. Concatenate side by side
        dashboard = np.hstack((panel1, panel2, panel3))
        return dashboard
