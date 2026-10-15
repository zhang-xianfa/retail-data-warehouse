package com.huimin.retail.common;

import lombok.Data;

/**
 * 统一响应结构：{code, msg, data}
 * 前端只需要判断 code == 200 即可，避免每个接口返回格式不一致。
 */
@Data
public class Result<T> {

    private int code;
    private String msg;
    private T data;

    public static <T> Result<T> success(T data) {
        Result<T> r = new Result<>();
        r.code = 200;
        r.msg = "success";
        r.data = data;
        return r;
    }

    public static <T> Result<T> fail(String msg) {
        Result<T> r = new Result<>();
        r.code = 500;
        r.msg = msg;
        return r;
    }
}
