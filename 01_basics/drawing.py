import cv2
import numpy as np

# --- ตัวแปร Global ---
points = []       # เก็บจุดที่กำลังคลิก (รอให้ครบ 2)
lines_list = []   # เก็บเส้นที่วาดเสร็จแล้ว [((x1, y1), (x2, y2)), ...]
mouse_pos = (0, 0) # เก็บตำแหน่งเมาส์ปัจจุบัน

def mouse_handler(event, x, y, flags, param):
    global points, lines_list, mouse_pos

    # อัปเดตตำแหน่งเมาส์ตลอดเวลาที่ขยับ
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_pos = (x, y)

    # 1. คลิกซ้าย: เลือกจุด / วาดเส้น
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"เพิ่มจุด: {x}, {y}")
        
        if len(points) == 2:
            lines_list.append((points[0], points[1])) # เก็บเข้าลิสต์เส้น
            points = [] # รีเซ็ตเพื่อรอคู่ใหม่
            print("วาดเส้นสำเร็จ!")

    # 2. คลิกขวา: ลบเส้นล่าสุด (Undo)
    elif event == cv2.EVENT_RBUTTONDOWN:
        if len(lines_list) > 0:
            lines_list.pop() # ลบเส้นสุดท้ายออก
            print("ลบเส้นล่าสุดออกแล้ว (Undo)")
        elif len(points) > 0:
            points.pop() # ถ้ามีจุดค้างอยู่ให้ลบจุดออกก่อน
            print("ยกเลิกจุดที่เลือกค้างไว้")

# สร้างหน้าต่างและเชื่อม Mouse Callback
cv2.namedWindow('Advanced Draw')

print("--- วิธีใช้งาน ---")
print("คลิกซ้าย 2 ครั้ง: วาดเส้น")
print("คลิกขวา: ลบเส้นล่าสุด (Undo)")
print("กด 'q': ออก | กด 'c': ล้างทั้งหมด")

while True:
    # สร้าง Canvas สีดำใหม่ทุกเฟรม (เพื่อให้ภาพอัปเดตตามการ Undo และ Overlay)
    img = np.zeros((600, 800, 3), np.uint8)
    cv2.setMouseCallback('Advanced Draw', mouse_handler)    
    # วาดเส้นทั้งหมดที่มีอยู่ใน List
    for pt1, pt2 in lines_list:
        cv2.line(img, pt1, pt2, (0, 255, 0), 2)

    # วาดจุดที่คลิกค้างไว้ (ถ้ามี)
    for p in points:
        cv2.circle(img, p, 4, (255, 255, 255), -1)

    # --- แสดงตำแหน่งเมาส์ที่มุมซ้ายบน ---
    text = f"Mouse: x={mouse_pos[0]}, y={mouse_pos[1]}"
    cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    # วาดเส้นตรงตามตำแหน่งเมาส์
    cv2.line(img, (mouse_pos[0], 0), (mouse_pos[0], img.shape[0]), (0, 255, 0), 1)
    cv2.line(img, (0, mouse_pos[1]), (img.shape[1], mouse_pos[1]), (0, 255, 0), 1)
    cv2.imshow('Advanced Draw', img)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        lines_list = []
        points = []

cv2.destroyAllWindows()