def number2string(total):
    total = "{:,.0f}".format(total)
    return total


def string2number(s):
    if not s:
        return 0
    # bỏ dấu phẩy ngăn cách hàng nghìn
    s = s.replace(",", "").strip()
    return float(s)
