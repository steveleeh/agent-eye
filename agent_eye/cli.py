import argparse
import json
import os
import cv2
import numpy as np

from .engine import ImageCompareEngine
from .visualizer import ImageCompareVisualizer

def generate_synthetic_images():
    """
    Generate synthetic 'mockup' and 'screenshot' images with deliberate layout, 
    color, and content mismatches to test the difference detection engine.
    """
    print("Generating synthetic test images...")
    
    # 1. Design Mockup (800x600)
    mockup = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Draw header bar (Dark Navy Blue)
    cv2.rectangle(mockup, (0, 0), (800, 60), (70, 35, 15), -1)
    cv2.putText(mockup, "Admin Dashboard", (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Draw Left Card (Sales Overview)
    cv2.rectangle(mockup, (50, 100), (350, 280), (220, 220, 220), 2)
    cv2.putText(mockup, "Sales Overview", (70, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2, cv2.LINE_AA)
    cv2.putText(mockup, "Total Sales: $12,450", (70, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
    cv2.putText(mockup, "Monthly Growth: +12.4%", (70, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
    # Green "Export" Button
    cv2.rectangle(mockup, (70, 230), (180, 260), (46, 139, 87), -1)  # Forest Green
    cv2.putText(mockup, "Export CSV", (88, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Draw Right Card (User Statistics)
    cv2.rectangle(mockup, (450, 100), (750, 280), (220, 220, 220), 2)
    cv2.putText(mockup, "User Statistics", (470, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2, cv2.LINE_AA)
    cv2.putText(mockup, "Active Users: 1,234", (470, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
    cv2.putText(mockup, "Pending Invites: 15", (470, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
    # Blue "Manage" Button
    cv2.rectangle(mockup, (470, 230), (580, 260), (200, 50, 50), -1)  # Blue
    cv2.putText(mockup, "Manage Users", (485, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    # 2. AI-Generated Screenshot (Slightly larger: 820x610, representing layout size drift)
    screenshot = np.ones((610, 820, 3), dtype=np.uint8) * 255
    
    # Draw header bar (slightly longer because width is 820)
    cv2.rectangle(screenshot, (0, 0), (820, 60), (70, 35, 15), -1)
    # MISMATCH 1: Typo in title ("Dashbord" instead of "Dashboard") and font size shift
    cv2.putText(screenshot, "Admin Dashbord", (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Draw Left Card
    cv2.rectangle(screenshot, (50, 100), (350, 280), (220, 220, 220), 2)
    cv2.putText(screenshot, "Sales Overview", (70, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2, cv2.LINE_AA)
    cv2.putText(screenshot, "Total Sales: $12,450", (70, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
    cv2.putText(screenshot, "Monthly Growth: +12.4%", (70, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
    # MISMATCH 2: Button shifted to the right by 40px and changed color to red-orange
    cv2.rectangle(screenshot, (70 + 40, 230), (180 + 40, 260), (50, 80, 240), -1)  # Red-Orange BGR
    cv2.putText(screenshot, "Export CSV", (88 + 40, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Draw Right Card
    cv2.rectangle(screenshot, (450, 100), (750, 280), (220, 220, 220), 2)
    cv2.putText(screenshot, "User Statistics", (470, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2, cv2.LINE_AA)
    # MISMATCH 3: Missing "Active Users: 1,234" text completely (representing layout omission)
    cv2.putText(screenshot, "Pending Invites: 15", (470, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
    # MISMATCH 4: Blue button is shifted DOWN by 15px
    cv2.rectangle(screenshot, (470, 230 + 15), (580, 260 + 15), (200, 50, 50), -1)
    cv2.putText(screenshot, "Manage Users", (485, 250 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    os.makedirs("test_data", exist_ok=True)
    cv2.imwrite("test_data/mockup.png", mockup)
    cv2.imwrite("test_data/screenshot.png", screenshot)
    print("Test images saved in 'test_data/' directory:")
    print("  - test_data/mockup.png")
    print("  - test_data/screenshot.png")
    
    return "test_data/mockup.png", "test_data/screenshot.png"

def main():
    parser = argparse.ArgumentParser(description="Agent-Eye: Visual difference analysis engine.")
    parser.add_argument("--mockup", type=str, help="Path to original design mockup image.")
    parser.add_argument("--screenshot", type=str, help="Path to screenshot image.")
    parser.add_argument("--align", type=str, default="pad", choices=["pad", "resize"], 
                        help="Alignment method for differing image sizes. Default: pad.")
    parser.add_argument("--threshold", type=int, default=30, 
                        help="SSIM difference threshold (0-255). Default: 30.")
    parser.add_argument("--dilation", type=int, default=18, 
                        help="Dilation size in pixels for clustering differences. Default: 18.")
    parser.add_argument("--min-area", type=int, default=35, 
                        help="Minimum area in pixels to register a change region. Default: 35.")
    parser.add_argument("--merge-dist", type=int, default=20, 
                        help="Max pixel distance to merge nearby diff boxes. Default: 20.")
    
    parser.add_argument("--out-annotated", type=str, default="diff_annotated.png", 
                        help="Output path for annotated screenshot. Default: diff_annotated.png.")
    parser.add_argument("--out-panel", type=str, default="diff_panel.png", 
                        help="Output path for multi-panel comparison dashboard. Default: diff_panel.png.")
    parser.add_argument("--out-json", type=str, default="diff_report.json", 
                        help="Output path for JSON discrepancy report. Default: diff_report.json.")
    parser.add_argument("--test", action="store_true", 
                        help="Run test with automatically generated synthetic images.")

    args = parser.parse_args()

    mockup_path = args.mockup
    screenshot_path = args.screenshot

    # If --test is selected or no arguments are provided, generate synthetic images
    if args.test or (not mockup_path and not screenshot_path):
        mockup_path, screenshot_path = generate_synthetic_images()

    if not mockup_path or not screenshot_path:
        parser.print_help()
        return

    print(f"\n--- Comparing Mockup & Screenshot ---")
    print(f"Mockup: {mockup_path}")
    print(f"Screenshot: {screenshot_path}")
    print(f"Settings: Align={args.align}, Thresh={args.threshold}, Dilation={args.dilation}, MinArea={args.min_area}, MergeDist={args.merge_dist}")

    # 1. Initialize Engine
    engine = ImageCompareEngine(
        threshold=args.threshold,
        dilation_size=args.dilation,
        min_area=args.min_area,
        merge_dist=args.merge_dist
    )

    # 2. Run Comparison
    results = engine.compare(mockup_path, screenshot_path, align_method=args.align)

    # 3. Save JSON Report
    report = {
        "overall_similarity_score": round(results["overall_similarity"], 4),
        "overall_mismatch_percentage": round(results["overall_mismatch_percentage"], 3),
        "regions_detected_count": len(results["regions"]),
        "mismatched_regions": results["regions"]
    }
    
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    print(f"✓ JSON Report written to: {args.out_json}")

    # 4. Generate Visualizations
    img1 = results["img1_aligned"]
    img2 = results["img2_aligned"]
    diff_mask = results["diff_mask"]
    thresh_mask = results["thresh_mask"]
    regions = results["regions"]

    # Draw individual annotated image
    annotated_img = ImageCompareVisualizer.draw_annotated_image(
        img2, regions, thresh_mask=thresh_mask, tint_weight=0.25
    )
    cv2.imwrite(args.out_annotated, annotated_img)
    print(f"✓ Annotated screenshot saved to: {args.out_annotated}")

    # Draw side-by-side dashboard panel
    panel = ImageCompareVisualizer.create_comparison_panel(img1, annotated_img, diff_mask)
    cv2.imwrite(args.out_panel, panel)
    print(f"✓ Side-by-side dashboard saved to: {args.out_panel}")

    # 5. Output Console Summary
    print(f"\n--- Analysis Summary ---")
    print(f"SSIM Similarity Index: {report['overall_similarity_score'] * 100:.2f}%")
    print(f"Total Discrepancy Area: {report['overall_mismatch_percentage']:.2f}% of canvas")
    print(f"Discrepant Regions Found: {report['regions_detected_count']}")
    
    for reg in report["mismatched_regions"]:
        box_str = f"x={reg['box'][0]}, y={reg['box'][1]}, w={reg['box'][2]}, h={reg['box'][3]}"
        pct_str = f"{int(reg['mismatch_ratio']*100)}%"
        print(f"  [{reg['severity']}] Region #{reg['id']}: Area {box_str} | local error {pct_str} | color diff {reg['mean_color_diff']:.1f}")
    print("------------------------\n")

if __name__ == "__main__":
    main()
