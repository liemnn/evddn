from sympy import symbols, sympify
import re
from datetime import datetime, timedelta,date

from odoo.exceptions import UserError

from . import  string_util,python_util

import logging
_logger = logging.getLogger(__name__)

def formula_get_variables(text):
    expr = sympify(text)
    return expr.free_symbols

def formula_is_if_else(formula):
    if formula:
        if re.search(r"\b(if|else)\b", formula, re.IGNORECASE):
            return True
    return False


def formula_tinhtoan_sotien(MAP,giaovien,cautruc_luong,parameters):
    result =None
    formula = cautruc_luong.formula
    formula = get_formula(formula,parameters)
    is_ifelse= formula_is_if_else(formula)
    try:
        if is_ifelse == False:
            #biểu thức không có if else
            variables = formula_get_variables(formula)
            if variables:
                for variable in variables:
                    key = str(variable)
                    if key in MAP:
                        data = MAP[str(variable)]
                        if data:
                            tien = data['tien']
                            if tien != None:
                                formula = formula.replace(str(variable), str(tien))
                            else:
                                return None
                        else:
                            return None

                    else:
                        raise UserError("Giáo viên [" + giaovien.name + "] "
                                                                        "thiết lập công thức lương lỗi. Bạn kiểm tra lại cấu trúc lương["
                                        + cautruc_luong.ma + "]")
            try:
                result = eval(formula)
            except Exception as e:
                print("Có lỗi xảy ra:",e)  # in thông báo lỗi
                _logger.error("Có lỗi xảy ra: %s", e)
                raise UserError("Có lỗi công thức cho giáo viên[" + giaovien.name + "] "
                                                                                    "thiết lập công thức lương lỗi. Bạn kiểm tra lại cấu trúc lương["
                                + cautruc_luong.ma + "]")


        else:
            variables = python_util.get_vars(formula)
            ctx = {}
            if variables:

                for variable in variables:
                    key = str(variable)
                    if key in MAP:
                        data = MAP[str(variable)]
                        if data:
                            tien = data['tien']
                            if tien != None:
                                ctx[key] = int(tien)
                            else:
                                return None
                        else:
                            return None

                    else:
                        raise UserError("Giáo viên [" + giaovien.name + "] "
                                                                        "thiết lập công thức lương lỗi. Bạn kiểm tra lại cấu trúc lương["
                                        + cautruc_luong.code + "]")
            try:
                result = python_util.eval_formula(formula, ctx)
            except Exception as e:
                print("Có lỗi xảy ra:", e)  # in thông báo lỗi
                _logger.error("Có lỗi xảy ra: %s", e)
                raise UserError("Có lỗi công thức cho giáo viên[" + giaovien.name + "] "
                                                                                    "thiết lập công thức lương lỗi. Bạn kiểm tra lại cấu trúc lương["
                                + cautruc_luong.code + "]")

        return result

    except Exception as e:
        print("Có lỗi xảy ra:", e)  # in thông báo lỗi
        _logger.error("Có lỗi xảy ra: %s", e)
        raise UserError("Có lỗi công thức cho giáo viên[" + giaovien.name + "] "
                                                                            "thiết lập công thức lương lỗi. Bạn kiểm tra lại cấu trúc lương["
                        + cautruc_luong.code + "]")

def get_formula(formula,parameters):
    if formula:
        if parameters:
            for key, value in parameters.items():
                if key.startswith("$"):
                    formula = formula.replace(key, str(value))
            if parameters.get('dilam_kehoachs'):
                formula = formula.replace('$NGAY_CONG_QUYDINH', str(len(parameters['dilam_kehoachs'])))


    return formula



def formula_get_desc(MAP,giaovien,cautruc_luong,parameters):
    formula = cautruc_luong.desc
    if not formula or formula == '':
        return ""
    formula = get_formula(formula, parameters)
    is_ifelse = formula_is_if_else(formula)

    if is_ifelse == False:
        #biểu thức không có if else
        return  formula

    else:

        try:
            return eval_formula_desc(formula,{})
        except Exception as e:
            print("Có lỗi xảy ra:", e)  # in thông báo lỗi
            _logger.error("Có lỗi xảy ra: %s", e)
            raise UserError(" Mô tả Có lỗi công thức cho giáo viên[" + giaovien.name + "] "
                                                                                "thiết lập công thức lương lỗi. Bạn kiểm tra lại cấu trúc lương["
                            + cautruc_luong.code + "]")
        return  ""


import re

def eval_formula_desc(formula: str, variables: dict = None):
    variables = variables or {}
    formula = formula.replace("\n", " ").strip()

    # Thay biến: $THAM_NIEN -> giá trị
    for k, v in variables.items():
        formula = formula.replace(f"${k}", str(v))

    # Chuẩn hóa AND / OR
    formula = formula.replace("AND", "and").replace("OR", "or")

    # IF
    if_match = re.search(
        r"IF\s*\((.*?)\)\s*KQ=\s*(.*?)(?=\s*ELSE\s*IF|\s*ELSE|$)",
        formula,
        re.IGNORECASE
    )

    if if_match:
        condition, result = if_match.groups()
        if eval(condition):
            return result.strip()

    # ELSE IF (có thể nhiều)
    elif_matches = re.findall(
        r"ELSE\s*IF\s*\((.*?)\)\s*KQ=\s*(.*?)(?=\s*ELSE\s*IF|\s*ELSE|$)",
        formula,
        re.IGNORECASE
    )

    for condition, result in elif_matches:
        if eval(condition):
            return result.strip()

    # ELSE
    else_match = re.search(r"ELSE\s*KQ=\s*(.*)$", formula, re.IGNORECASE)
    if else_match:
        return else_match.group(1).strip()

    return None



def num_to_vietnamese(n):
    units = ["", "nghìn", "triệu", "tỷ"]
    digits = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def read_three_digits(num):
        hundred = num // 100
        ten = (num % 100) // 10
        unit = num % 10
        result = ""
        if hundred > 0:
            result += digits[hundred] + " trăm "
        if ten > 1:
            result += digits[ten] + " mươi "
        elif ten == 1:
            result += "mười "
        if unit > 0:
            result += digits[unit]
        return result.strip()

    parts = []
    i = 0
    while n > 0:
        num = n % 1000
        if num > 0:
            parts.append(read_three_digits(num) + " " + units[i])
        n //= 1000
        i += 1
    return " ".join(reversed(parts)).strip() + " đồng./"



if __name__ == "__main__":
    # gọi thử hàm
    text ="IF 3.1<1 KQ =((2.0*70000)+(1.0*100000)) ELSE KQ =((2.0*100000)+(1.0*150000))"
    #result = ti(number)
    #print("Kết quả:", result)