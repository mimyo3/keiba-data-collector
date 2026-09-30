import time
from heavy_process import process_large_data

def test_correctness_and_performance():
    data = list(range(1000))
    
    start = time.time()
    res = process_large_data(data)
    elapsed = time.time() - start

    # 正当性検証
    assert len(res) == 1000
    assert res[0] == 0   # 0 * 2
    assert res[1] == 3   # 1 * 3
    
    # パフォーマンス検証（1秒未満で終わること）
    assert elapsed < 1.0, f"処理が重すぎます: {elapsed:.2f}秒"
