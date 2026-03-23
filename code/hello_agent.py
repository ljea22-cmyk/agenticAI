#!/usr/bin/env python3
"""
Hello Agent - 현재 시간을 output/hello.txt에 저장하는 스크립트
"""

from datetime import datetime
import os

def main():
    # 현재 시각 가져오기
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # output 폴더 경로
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    output_file = os.path.join(output_dir, 'hello.txt')
    
    # 파일에 현재 시각 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Hello from Agent!\n")
        f.write(f"Current time: {current_time}\n")
    
    print(f"✅ Success! Current time saved to {output_file}")
    print(f"📝 Time: {current_time}")

if __name__ == "__main__":
    main()
