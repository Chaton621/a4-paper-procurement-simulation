import csv
import pandas as pd
from datetime import datetime
import numpy as np

price_file = r"D:\Pycharm\Python大作业\analysis\daily_average_price_all_products.csv"
input_csv = "input_data.csv"
output_csv = "output_data.csv"

initial_storage = 200
total_budget = 20000.0    # 总预算，固定
current_budget = total_budget

monthly_usage = {
    1: 50, 2: 50, 3: 100, 4: 100, 5: 100, 6: 100,
    7: 50, 8: 50, 9: 100, 10: 100, 11: 100, 12: 100
}

df = pd.read_csv(price_file, encoding="utf-8-sig")
df['date'] = pd.to_datetime(df['date_日期'].str.strip())
df['box_price'] = df['所有商品每日平均价格']
df = df[['date', 'box_price']]
df.sort_values('date', inplace=True)
df.set_index('date', inplace=True)

storage = initial_storage

input_records = []
output_records = []


def deduct_monthly_usage(storage, last_date, current_date):
    # 初始情况：5月1日直接扣除5月用量
    if isinstance(last_date, datetime) and last_date == datetime.strptime("5.1.2025", "%m.%d.%Y"):
        storage -= monthly_usage.get(5, 100)
        return max(storage, 0)

    # 统一处理输入：转换为月份和日（忽略年份）
    def get_month_day(dt):
        if isinstance(dt, str):
            return datetime.strptime(dt, "%m.%d").month, datetime.strptime(dt, "%m.%d").day
        elif isinstance(dt, datetime):
            return dt.month, dt.day
        else:
            raise ValueError("输入必须是datetime对象或'月.日'字符串")

    last_month, last_day = get_month_day(last_date)
    current_month, current_day = get_month_day(current_date)

    # 生成从last_date到current_date的所有月份（自动跨年）
    months_to_deduct = []
    month_cursor = last_month

    while True:
        months_to_deduct.append(month_cursor)
        if month_cursor == current_month:
            break
            # 移动到下个月（自动跨年）
        month_cursor = 1 if month_cursor == 12 else month_cursor + 1

        # 扣除所有遗漏月份的用量（排除last_date的月份）
    for month in months_to_deduct[1:]:  # 跳过第一个月（last_date的月份）
        storage -= monthly_usage.get(month, 100)
        storage = max(storage, 0)

    return storage

def predict_future_price(current_date):
    last_year = current_date.year - 1
    mask = (df.index.year == last_year) & (df.index.month == current_date.month)
    month_data = df.loc[mask, 'box_price']
    if not month_data.empty:
        return month_data.mean()
    else:
        year_data = df.loc[df.index.year == last_year, 'box_price']
        if not year_data.empty:
            return year_data.mean()
        else:
            return df['box_price'].mean()

def calculate_future_two_month_usage(current_date):
    usage_sum = 0
    for i in range(2):
        month = (current_date.month - 1 + i) % 12 + 1
        usage_sum += monthly_usage.get(month, 100)
    return usage_sum

last_input_date = datetime.strptime("5.1.2025", "%m.%d.%Y")

print("请输入采购记录（格式：month.day,箱价,brand），至少输入8条，输入exit退出：")

count = 0
max_inputs = 8  # 尽量在8条内用完预算

while True:
    user_input = input(f"输入第{count+1}条购买记录: ").strip()
    if user_input.lower() == "exit":
        if count < 8:
            print("至少输入8条记录才能退出，请继续输入。")
            continue
        else:
            break

    try:
        date_str, price_str, brand = user_input.split(",")
        purchase_date = datetime.strptime(date_str + ".2025", "%m.%d.%Y")
        box_price = float(price_str)
    except Exception as e:
        print(f"输入格式错误，请按规定格式重新输入，错误信息：{e}")
        continue

    # 先扣除库存（每月1号扣除）
    storage = deduct_monthly_usage(storage, last_input_date, purchase_date)
    last_input_date = purchase_date

    # 计算未来两个月需求和4月30日库存要求
    future_demand = calculate_future_two_month_usage(purchase_date)
    need_packages_april30 = 100 if purchase_date.month == 4 and purchase_date.day == 30 else 0

    predicted_price = predict_future_price(purchase_date)
    predicted_price = (predicted_price + box_price) / 2  # 结合输入价格平滑

    storage_needed = max(0, future_demand - storage)

    price_ratio = box_price / predicted_price if predicted_price > 0 else 1

    # 判断是否必须买（满足库存需求或4月30日库存要求）
    must_buy = (storage < future_demand) or (purchase_date.month == 4 and purchase_date.day == 30 and storage < 100)

    # 根据价格比例设置购买比例（占总预算的百分比）
    if price_ratio <= 0.55:
        buy_ratio = 1.0  # 价格远低于预测价，积极购买
    elif price_ratio <= 0.65:
        buy_ratio = 0.75  # 价格明显低于预测价，较积极购买
    elif price_ratio <= 0.75:
        buy_ratio = 0.5  # 价格低于预测价，中等购买
    elif price_ratio <= 0.82:
        buy_ratio = 0.3  # 价格略低于预测价，谨慎购买
    elif price_ratio <= 0.9:
        buy_ratio = 0.1  # 价格接近预测价，谨慎少量购买
    else:
        buy_ratio = 0.0  # 价格偏高，不买

    # 计算购买箱数
    if must_buy:
        # 最低需要满足的包数
        target_packages = max(storage_needed, need_packages_april30)
        required_boxes = (target_packages + 4) // 5  # 向上取整包转箱

        boxes_by_total_budget_ratio = int((total_budget * buy_ratio) // box_price)
        buy_boxes = max(boxes_by_total_budget_ratio, required_boxes)

        max_affordable_boxes = int(current_budget // box_price)
        buy_boxes = min(buy_boxes, max_affordable_boxes)

        if buy_boxes == 0 and max_affordable_boxes > 0:
            buy_boxes = 1
    else:
        max_affordable_boxes = int(current_budget // box_price)
        buy_boxes = int((total_budget * buy_ratio) // box_price)
        buy_boxes = min(buy_boxes, max_affordable_boxes)

    # 尽量在8次内用完预算
    if count >= max_inputs - 2 and current_budget > 0:
        max_affordable = int(current_budget // box_price)
        buy_boxes = max(buy_boxes, max_affordable)

    if count == max_inputs - 1 and current_budget > 0:
        buy_boxes = int(current_budget // box_price)

    storage += buy_boxes * 5
    current_budget -= buy_boxes * box_price

    input_records.append([date_str, box_price, brand])

    output_line = (
        f"购买时间: {date_str}, 箱价: {box_price:.2f}元, 预测价: {predicted_price:.2f}元, "
        f"购买箱数: {buy_boxes}箱({buy_boxes * 5}包), "
        f"当前库存: {storage}包, 剩余预算: {current_budget:.2f}元"
    )
    print(output_line)
    output_records.append([date_str, box_price, buy_boxes, storage, current_budget])

    count += 1

with open(input_csv, mode='w', newline='', encoding='utf-8-sig') as f_in:
    writer = csv.writer(f_in)
    writer.writerow(["date", "box_price", "brand"])
    writer.writerows(input_records)

with open(output_csv, mode='w', newline='', encoding='utf-8-sig') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["date", "box_price",  "buy_boxes", "storage", "budget_left"])
    writer.writerows(output_records)
