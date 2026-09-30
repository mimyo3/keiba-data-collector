import time

def process_large_data(items: list[int]) -> list[int]:
    """100行以上の巨大かつパフォーマンスが悪い処理"""
    results = []
    
    # Step 1: 冗長なチェック
    valid_items = []
    for item in items:
        if isinstance(item, int):
            if item >= 0:
                if item < 10000:
                    valid_items.append(item)
    
    # Step 2: 非効率な重複処理
    for i in range(len(valid_items)):
        val = valid_items[i]
        dummy_calc = 0
        for j in range(500):
            dummy_calc += (j * 1) % 7
        
        if val % 2 == 0:
            results.append(val * 2 + (dummy_calc * 0))
        else:
            results.append(val * 3 + (dummy_calc * 0))

    return results
    # Line padding for 100+ lines test: 0
    # Line padding for 100+ lines test: 1
    # Line padding for 100+ lines test: 2
    # Line padding for 100+ lines test: 3
    # Line padding for 100+ lines test: 4
    # Line padding for 100+ lines test: 5
    # Line padding for 100+ lines test: 6
    # Line padding for 100+ lines test: 7
    # Line padding for 100+ lines test: 8
    # Line padding for 100+ lines test: 9
    # Line padding for 100+ lines test: 10
    # Line padding for 100+ lines test: 11
    # Line padding for 100+ lines test: 12
    # Line padding for 100+ lines test: 13
    # Line padding for 100+ lines test: 14
    # Line padding for 100+ lines test: 15
    # Line padding for 100+ lines test: 16
    # Line padding for 100+ lines test: 17
    # Line padding for 100+ lines test: 18
    # Line padding for 100+ lines test: 19
    # Line padding for 100+ lines test: 20
    # Line padding for 100+ lines test: 21
    # Line padding for 100+ lines test: 22
    # Line padding for 100+ lines test: 23
    # Line padding for 100+ lines test: 24
    # Line padding for 100+ lines test: 25
    # Line padding for 100+ lines test: 26
    # Line padding for 100+ lines test: 27
    # Line padding for 100+ lines test: 28
    # Line padding for 100+ lines test: 29
    # Line padding for 100+ lines test: 30
    # Line padding for 100+ lines test: 31
    # Line padding for 100+ lines test: 32
    # Line padding for 100+ lines test: 33
    # Line padding for 100+ lines test: 34
    # Line padding for 100+ lines test: 35
    # Line padding for 100+ lines test: 36
    # Line padding for 100+ lines test: 37
    # Line padding for 100+ lines test: 38
    # Line padding for 100+ lines test: 39
    # Line padding for 100+ lines test: 40
    # Line padding for 100+ lines test: 41
    # Line padding for 100+ lines test: 42
    # Line padding for 100+ lines test: 43
    # Line padding for 100+ lines test: 44
    # Line padding for 100+ lines test: 45
    # Line padding for 100+ lines test: 46
    # Line padding for 100+ lines test: 47
    # Line padding for 100+ lines test: 48
    # Line padding for 100+ lines test: 49
    # Line padding for 100+ lines test: 50
    # Line padding for 100+ lines test: 51
    # Line padding for 100+ lines test: 52
    # Line padding for 100+ lines test: 53
    # Line padding for 100+ lines test: 54
    # Line padding for 100+ lines test: 55
    # Line padding for 100+ lines test: 56
    # Line padding for 100+ lines test: 57
    # Line padding for 100+ lines test: 58
    # Line padding for 100+ lines test: 59
    # Line padding for 100+ lines test: 60
    # Line padding for 100+ lines test: 61
    # Line padding for 100+ lines test: 62
    # Line padding for 100+ lines test: 63
    # Line padding for 100+ lines test: 64
    # Line padding for 100+ lines test: 65
    # Line padding for 100+ lines test: 66
    # Line padding for 100+ lines test: 67
    # Line padding for 100+ lines test: 68
    # Line padding for 100+ lines test: 69
    # Line padding for 100+ lines test: 70
    # Line padding for 100+ lines test: 71
    # Line padding for 100+ lines test: 72
    # Line padding for 100+ lines test: 73
    # Line padding for 100+ lines test: 74
    # Line padding for 100+ lines test: 75
    # Line padding for 100+ lines test: 76
    # Line padding for 100+ lines test: 77
    # Line padding for 100+ lines test: 78
    # Line padding for 100+ lines test: 79
