import os
import csv
import subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count
import time

# 配置路径
ffdec_path = "ffdec"
swf_dir = "icon"
symbols_dir = "iconsymbol"
output_dir = "iconImage"
MAX_WORKERS = cpu_count()

# 创建输出目录
Path(output_dir).mkdir(parents=True, exist_ok=True)

def find_item_frame(csv_path):
    """定位item符号ID"""
    with open(csv_path, "r") as f:
        csv_reader = csv.reader(f, delimiter=';')
        for row in csv_reader:
            if len(row) >= 2 and row[1].strip().lower() == "item":
                try:
                    return int(row[0])
                except ValueError:
                    continue
    return None

def process_swf(swf_file):
    """处理单个SWF文件"""
    swf_stem = swf_file.stem
    try:
        csv_path = Path(symbols_dir) / f"{swf_stem}.swf" / "symbols.csv"
        
        if not csv_path.exists():
            return (False, f"符号表缺失 {swf_stem}")
        
        symbol_id = find_item_frame(csv_path)
        if symbol_id is None:
            return (False, f"未找到item符号 {swf_stem}")
        
        # 构造带有帧号的输出路径
        temp_dir = Path(output_dir) / "temp" / swf_stem
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        command = [
            ffdec_path, "-cli",
            "-selectid", str(symbol_id),
            "-zoom", "4",
            "-export", "sprite",
            str(temp_dir.resolve()),  # 指定临时目录
            str(swf_file.resolve())
        ]
        
        subprocess.run(command, check=True, capture_output=True, timeout=30)
        
        # 后处理：查找实际生成的PNG文件
        output_path = Path(output_dir) / f"{swf_stem}.png"
        png_files = list(temp_dir.rglob("*.png"))
        
        if png_files:
            # 移动第一个找到的PNG文件
            png_files[0].rename(output_path)
            # 清理临时目录
            subprocess.run(["rm", "-rf", str(temp_dir)])
            return (True, f"成功导出 {swf_stem}")
        else:
            return (False, f"无PNG生成 {swf_stem}")

    except Exception as e:
        return (False, f"错误 {swf_stem}: {str(e)}")

if __name__ == "__main__":
    start_time = time.time()
    
    swf_files = list(Path(swf_dir).glob("*.swf"))
    print(f"待处理文件数: {len(swf_files)}")
    
    with Pool(processes=MAX_WORKERS) as pool:
        success = 0
        results = pool.imap_unordered(process_swf, swf_files)
        for i, (status, msg) in enumerate(results, 1):
            print(f"[{i}/{len(swf_files)}] {msg}")
            success += int(status)
    
    print(f"\n完成！成功率: {success}/{len(swf_files)}")
    print(f"总耗时: {time.time() - start_time:.1f}s")