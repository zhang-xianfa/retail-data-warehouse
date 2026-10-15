package com.huimin.retail.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 跨域配置。
 * 页面若以 file:// 方式打开、或部署在其他端口，浏览器会按同源策略拦截 ajax 请求，
 * 需要服务端在响应头中返回 Access-Control-Allow-Origin。
 * （更规范的做法是把前端页面直接放到 src/main/resources/static 下与后端同源部署。）
 */
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("*")
                .allowedMethods("GET", "POST", "OPTIONS")
                .allowedHeaders("*")
                .maxAge(3600);
    }
}
