import os
import argparse
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def get_directory() -> Path:
    """
    获取用户输入的目录路径，并处理绝对路径和相对路径，检查目录是否存在和可读性。
    """
    parser = argparse.ArgumentParser(description="处理 CSV 文件并计算平均值。")
    parser.add_argument("directory", help="包含 CSV 文件的目录")
    args = parser.parse_args()
    directory = Path(args.directory).expanduser().absolute()  # 使用 pathlib 处理路径

    if not directory.exists():
        raise ValueError(f"输入的目录 '{directory}' 不存在。")
    if not directory.is_dir():
        raise ValueError(f"输入的路径 '{directory}' 不是一个有效的目录。")
    if not os.access(directory, os.R_OK):
        raise ValueError(f"没有权限读取目录 '{directory}'。")

    return directory


def remove_final_csv(directory: Path):
    """
    删除目录下的 final.csv 文件（如果存在）。
    """
    final_csv_name = f"{directory.name}.csv"
    final_csv_path = directory / final_csv_name  # 使用 / 运算符连接路径
    if final_csv_path.exists():
        final_csv_path.unlink()
        print(f"'{final_csv_name}' 已删除。")
    else:
        print(f"'{final_csv_name}' 不存在。")


def process_csv_files(directory: Path):
    """
    读取目录下的所有 CSV 文件，计算平均值，并保存到 final.csv。
    """
    csv_files = list(directory.glob("*.csv"))  # 使用 pathlib 的 glob 方法
    if not csv_files:
        raise ValueError(f"在目录 '{directory}' 中没有找到 CSV 文件。")
    print(f"找到以下 CSV 文件：{[str(f) for f in csv_files]}")

    final_csv_name = f"{directory.name}.csv"
    final_csv_path = directory / final_csv_name
    # 过滤掉 final.csv，避免重复处理
    csv_files = [file for file in csv_files if file != final_csv_path]
    dataframes = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            # 清理列名和数据
            df.columns = [col.strip() for col in df.columns]
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            dataframes.append(df)
        except Exception as e:
            print(f"读取文件 '{file}' 时出错: {e}")
            # 如果没有成功读取任何 CSV 文件，直接返回
            if not dataframes:
                print("没有成功读取任何 CSV 文件，跳过计算。")
                return
            continue

    if not dataframes:
        print("没有可用的数据进行处理。")
        return

    combined_df = pd.concat(dataframes, ignore_index=True)
    # 对 'Frequency(Hz)' 列进行分组，并计算 'Magnitude(dB)' 的平均值
    final_df = combined_df.groupby("Frequency(Hz)", as_index=False).agg(
        {"Magnitude(dB)": lambda x: round(x.mean(), 6)}
    )

    final_df.to_csv(final_csv_path, index=False)
    print(f"结果已保存到 '{final_csv_path}'。")


def show_gui(file_path):
    """
    读取 final.csv 文件，并使用 GUI 展示数据图。
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"读取文件 '{file_path}' 时出错: {e}")
        return

    if "Frequency(Hz)" not in df.columns or "Magnitude(dB)" not in df.columns:
        print("CSV 文件缺少必要的列 'Frequency(Hz)' 或 'Magnitude(dB)'。")
        return

    # 创建主窗口
    root = tk.Tk()
    root.title("CSV Data Plot")

    # 创建 Matplotlib figure 和 axes
    fig, ax = plt.subplots(figsize=(8, 6))
    # 绘制散点图，x轴使用对数刻度
    ax.scatter(df["Frequency(Hz)"], df["Magnitude(dB)"], marker="o", linestyle="-")
    ax.set_xscale("log")
    ax.set_xlabel("Frequency(Hz) [log scale]")
    ax.set_ylabel("Magnitude(dB)")
    ax.set_title("Frequency vs Magnitude")
    ax.grid(True)

    # 创建 Canvas
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # 修改窗口关闭事件处理函数
    def on_closing():
        root.destroy()
        root.quit() # 退出 tkinter 主循环
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 运行主循环
    root.mainloop()



def main():
    """
    主函数，执行整个流程。
    """
    try:
        directory = get_directory()
        remove_final_csv(directory)
        process_csv_files(directory)
        final_csv_name = f"{directory.name}.csv"
        final_csv_path = directory / final_csv_name
        if final_csv_path.exists():
            show_gui(final_csv_path)
        else:
            print("未生成 final.csv 文件，无法展示图形界面。")
    except ValueError as e:
        print(f"错误: {e}")
        exit(1)  # 发生 ValueError 时终止程序
    except Exception as e:
        print(f"发生未知错误: {e}")
        exit(1)


if __name__ == "__main__":
    main()