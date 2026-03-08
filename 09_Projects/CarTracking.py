import cv2 
from ultralytics import YOLO 



lane_points = []
mouse_pos = (0, 0)
# ฟังก์ชันรับเหตุการณ์จากเมาส์ เพื่อใช้ระบุพิกัดและคำนวณความชันของเลน
def mouse_callback(event, x, y, flags, param):
    global lane_points, mouse_pos
    if event == cv2.EVENT_LBUTTONDOWN:
        # ปรับพิกัดกลับไปเป็นขนาดดั้งเดิมของวิดีโอ
        orig_x = int(x / ratio)
        orig_y = int(y / ratio)
        print(f"คลิกเมาส์ที่: X={orig_x}, Y={orig_y}")
        lane_points.append((orig_x, orig_y))

        if len(lane_points) == 2:
            # คำนวณความชัน (slope) และจุดตัดแกน x (intercept) จากจุด 2 จุดที่เลือก
            x1, y1 = lane_points[0]
            x2, y2 = lane_points[1]

            if y2 != y1:  # ป้องกันการหารด้วยศูนย์
                slope = (x2 - x1) / (y2 - y1)
                intercept = x2 - slope * y2
                print(f"\nคำนวณเส้นแบ่งเลนเสร็จสิ้น:")
                print(f"ความชัน (slope) = {slope:.3f}")
                print(f"จุดตัด (intercept) = {intercept:.1f}")
                print(f"สมการเส้นตรง: x = {slope:.3f} * y + {intercept:.1f}")

            lane_points.clear()  # ล้างพิกัดเพื่อเริ่มคำนวณใหม่ในครั้งถัดไป
    if event == cv2.EVENT_MOUSEMOVE:
        # ปรับพิกัดกลับไปเป็นขนาดดั้งเดิมของวิดีโอ เพื่อให้ตัวเลขที่แสดงตรงกับสเกลจริงของวิดีโอ
        orig_x = int(x / ratio)
        orig_y = int(y / ratio)
        mouse_pos = (orig_x, orig_y)

def get_lane_divider_x(y):
    """คำนวณค่า x ของเส้นแบ่งเลน ณ ค่า y ที่กำหนด"""
    return int(lane_divider_slope * y + lane_divider_intercept)

def draw_sloped_lane_divider(frame, y_start, y_end):
    """วาดเส้นแบ่งเลนที่มีความชันตามพิกัดขอบถนน"""
    x_start = get_lane_divider_x(y_start)
    x_end = get_lane_divider_x(y_end)
    cv2.line(frame, (x_start, y_start), (x_end, y_end), (255, 255, 255), 3)


# ตั้งค่าตัวแปรเบื้องต้น
ratio = 0.5  # สัดส่วนการย่อ/ขยายรูปภาพสำหรับแสดงผล
line_y_in = 1300      # ตำแหน่งเส้นแนวนอนสำหรับรถขาเข้า
line_y_out = line_y_in   # ตำแหน่งเส้นแนวนอนสำหรับรถขาออก
lane_divider_slope = 0.402    # ความชันของเส้นแบ่งเลน (ได้จากการคำนวณล่วงหน้า)
lane_divider_intercept = 1457.4  # จุดตัดแกน x ของเส้นแบ่งเลน
divider_x_at_out = get_lane_divider_x(line_y_out)
divider_x_at_in = get_lane_divider_x(line_y_in)
name = "YOLO car count"
in_count = 0
out_count = 0
track_history = {}  # เก็บพิกัดก่อนหน้าของแต่ละ Track ID
counted_ids = set() # เก็บ ID ที่ถูกนับไปแล้วเพื่อป้องกันการนับซ้ำ

# โหลดโมเดล YOLO (ในที่นี้ใช้เวอร์ชัน 12)
model = YOLO("yolo12l.pt")

# เปิดวิดีโอจากไฟล์
cap = cv2.VideoCapture("../assets/vehicle-counting.mp4")
cv2.namedWindow(name)
cv2.setMouseCallback(name, mouse_callback)

while cap.isOpened():
    # อ่านเฟรมจากวิดีโอ
    ret, frame = cap.read()
    if not ret:
        break

    draw_sloped_lane_divider(frame, y_start=700, y_end=frame.shape[0])
    # วาดเส้นตรวจจับ (ใช้พิกัดจริงของวิดีโอ)
    cv2.line(frame, (0, line_y_in), (frame.shape[1], line_y_in), (0, 0, 255), 2)
    # ปรับขนาดเฟรมเพื่อให้แสดงผลได้พอดีหน้าจอ
    new_heigth = frame.shape[0] * ratio
    new_width = frame.shape[1] * ratio
    frame = cv2.resize(frame, (int(new_width), int(new_heigth)))
    # แสดงพิกัดเมาส์
    text = f"Mouse: x={mouse_pos[0]}, y={mouse_pos[1]}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    # แสดงจำนวนรถ
    cv2.putText(frame, f"In: {in_count}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"Out: {out_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    # รันการติดตามวัตถุ (Tracking) โดยกรองเฉพาะรถ (class 2) และใช้ GPU (device 0)
    results = model.track(frame, persist=True, classes=[2], device=0, verbose=False)
    
    # ตรวจสอบว่าตรวจพบวัตถุหรือไม่
    if results[0].boxes.data is not None:
        # ดึงพิกัดกล่อง (xyxy), เลข ID ของการติดตาม (track_ids), เลขคลาส (class_indices),และค่าความเชื่อมั่น (confidences)
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy()
        class_indices = results[0].boxes.cls.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        
        for box, track_id, class_index, confidence in zip(boxes, track_ids, class_indices, confidences):
            x1, y1, x2, y2 = box
            cx = int((x1 + x2) * 0.5)
            cy = int((y1 + y2) * 0.5)
            
            # แปลงพิกัดกลับเป็นขนาดจริงเพื่อใช้เปรียบเทียบกับ line_y
            real_cy = cy / ratio
            real_cx = cx / ratio

            # ตรวจสอบการข้ามเส้น
            if track_id in track_history:
                prev_real_cy = track_history[track_id]
                
                # ถ้า cy ข้ามเส้น line_y_in/out
                if prev_real_cy < line_y_in and real_cy >= line_y_in:
                    if track_id not in counted_ids:
                        # แบ่งเลนด้วยความชัน
                        divider_x = get_lane_divider_x(real_cy)
                        if real_cx < divider_x:
                            out_count += 1
                        else:
                            in_count += 1
                        counted_ids.add(track_id)
                elif prev_real_cy > line_y_in and real_cy <= line_y_in:
                     if track_id not in counted_ids:
                        divider_x = get_lane_divider_x(real_cy)
                        if real_cx < divider_x:
                            out_count += 1
                        else:
                            in_count += 1
                        counted_ids.add(track_id)

            track_history[track_id] = real_cy

            print(f"Track ID: {track_id}, Class: {class_index}, Confidence: {confidence}")
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            class_name = model.names[int(class_index)]
            cv2.putText(frame, f"Class: {class_name} Track ID: {int(track_id)}", (int(x1), int(y1)-10), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 0), 1)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
           
    

    # แสดงผลเฟรมวิดีโอ
    cv2.imshow(name, frame)
    # กดปุ่ม 'q' เพื่อออกจากลูป
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    

cap.release()
cv2.destroyAllWindows()