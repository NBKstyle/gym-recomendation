from flask import Flask, render_template, request, redirect, url_for
import pandas as pd

app = Flask(__name__)

# Load exercise data (chỉnh sửa đường dẫn phù hợp)
exercise_data = pd.read_csv('D:/DoanGIS/excel/dulieudauvao/Exercise_data.csv')
exercise_data['exercise_type'] = exercise_data['exercise_type'].fillna('Main')

# Hàm tính BMI
def calculate_bmi(weight, height):
    bmi = weight / (height ** 2)
    if bmi < 18.5:
        status = "Bạn có vẻ đang thiếu cân. Bạn cố gắng bổ sung thêm khẩu phần ăn mỗi ngày nhé!"
    elif 18.5 <= bmi < 24.9:
        status = "Chúc mừng bạn! Bạn không có dấu hiệu thiếu hay thừa cân"
    elif 25 <= bmi < 29.9:
        status = "Bạn đang trong tình trạng thừa cân. Hãy giảm bớt khẩu phần ăn và tập luyện chăm chỉ hơn nhé!"
    else:
        status = "Bạn đang trong tình trạng béo phì. Hãy đến trang tư vấn sức khỏe để được tư vấn trước khi chọn mục tiêu tập luyện"
    return bmi, status

# Hàm xử lý việc đề xuất bài tập cho người dùng
def recommend_exercises_30_sessions(user_data):
    goals = user_data['Goals']
    gender = user_data['Gender']
    available_time = user_data['Daily Minutes']

    # Lọc dữ liệu theo giới tính và mục tiêu
    gender_filter = exercise_data['Gender'].str.contains(gender, case=False, na=False)
    goal_filter = exercise_data['Goal'].apply(lambda x: any(g in x for g in goals))
    filtered_data = exercise_data[gender_filter & goal_filter].copy()

    # Kiểm tra nếu không có bài tập sau khi lọc
    if filtered_data.empty:
        print("Không có bài tập nào phù hợp với mục tiêu và giới tính của bạn.")
        return []

    # Tính thời gian tổng mỗi bài tập (phút), cộng thêm thời gian nghỉ giữa các bài tập
    filtered_data['Total_time'] = (
        (filtered_data['Rep_time'] * filtered_data['Reps'] * filtered_data['Sets'] +
         (filtered_data['Sets'] - 1) * filtered_data['Rest_time']) / 60
    )
    
    # Phân loại bài tập theo `exercise_type` và `level`
    warm_up = filtered_data[filtered_data['exercise_type'] == 'Warm-up']
    relax = filtered_data[filtered_data['exercise_type'] == 'Relax']
    main_easy_medium = filtered_data[
        (filtered_data['exercise_type'] == 'Main') & 
        (filtered_data['Level'].isin(['Easy', 'Medium']))
    ]
    main_difficulty = filtered_data[
        (filtered_data['exercise_type'] == 'Main') & 
        (filtered_data['Level'] == 'Difficulty')
    ]

    rest_between_exercises = 3  # Thời gian nghỉ giữa các bài tập (phút)
    sessions = []

    for session_num in range(1, 31):
        session_time = available_time
        session_plan = []

        # Ưu tiên bài khởi động
        for _, row in warm_up.head(3).iterrows():
            if session_time >= row['Total_time'] + rest_between_exercises:
                session_plan.append(row)
                session_time -= (row['Total_time'] + rest_between_exercises)

        # Chọn bài tập chính dựa trên mức độ khó
        if session_num <= 18:  # 18 buổi đầu
            main_exercises = main_easy_medium.sample(frac=1).reset_index(drop=True)
        else:  # 12 buổi cuối
            main_exercises = pd.concat([ 
                main_easy_medium.sample(frac=1),
                main_difficulty.sample(n=min(2, len(main_difficulty)), random_state=session_num)
            ]).reset_index(drop=True)

        for _, row in main_exercises.iterrows():
            if session_time >= row['Total_time'] + rest_between_exercises:
                session_plan.append(row)
                session_time -= (row['Total_time'] + rest_between_exercises)

        # Thêm bài giãn cơ
        for _, row in relax.head(3).iterrows():
            if session_time >= row['Total_time'] + rest_between_exercises:
                session_plan.append(row)
                session_time -= (row['Total_time'] + rest_between_exercises)

        # Lưu kế hoạch buổi tập
        if not session_plan:
            print(f"Buổi {session_num}: Không có bài tập nào phù hợp với thời gian tập luyện của bạn.")
            sessions.append([]) 
        else:
            sessions.append(session_plan)

    return sessions

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


