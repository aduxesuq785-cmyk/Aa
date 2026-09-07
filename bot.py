#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ARIYAN: both original HTML pages bundled in one Python 3 file.

Run: python Ariyan.py
User: http://127.0.0.1:8000/
Admin: http://127.0.0.1:8000/admin
Railway Start Command: python Ariyan.py
Railway/Python hosts: put a requirements.txt containing only a comment beside this file
to enable Python detection. No third-party dependencies are required.
Default bind: 0.0.0.0; PORT is read from the environment (fallback: 8000).
Local-only option: python Ariyan.py --host 127.0.0.1
Optional custom port: python Ariyan.py --port 8080
Health check path: /healthz
Domain target ports must match the listening port printed at startup.
No pip packages or separate HTML files are required.
The original Firebase backend and external assets still require internet.
HTML, CSS, JavaScript, configuration and existing behavior are preserved.
"""

import argparse
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

USER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Shop - Premium Store</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 50%, #0a0a0a 100%);
      color: #e0e0e0;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Loading Overlay */
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      backdrop-filter: blur(10px);
      z-index: 10000;
      display: none;
      align-items: center;
      justify-content: center;
      animation: fadeIn 0.3s ease;
    }

    .loading-overlay.active {
      display: flex;
    }

    .loading-content {
      text-align: center;
    }

    .loading-spinner {
      width: 60px;
      height: 60px;
      border: 5px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: #00ffff;
      animation: spin 1s linear infinite;
      margin: 0 auto 20px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .loading-text {
      color: #00ffff;
      font-size: 18px;
      animation: pulse 1.5s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    /* Notification Toast */
    .notification-toast {
      position: fixed;
      top: 80px;
      right: 20px;
      background: rgba(0, 0, 0, 0.95);
      border: 1px solid #00ffff;
      border-radius: 12px;
      padding: 15px 20px;
      color: #00ffff;
      z-index: 10001;
      display: none;
      animation: slideInRight 0.4s ease;
      box-shadow: 0 8px 32px rgba(0, 255, 255, 0.4);
      max-width: 350px;
      backdrop-filter: blur(20px);
    }

    @keyframes slideInRight {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .notification-toast.show {
      display: block;
    }

    .notification-toast.success {
      border-color: #00ff88;
      color: #00ff88;
    }

    .notification-toast.error {
      border-color: #ff006e;
      color: #ff006e;
    }

    /* Header */
    .header {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding: 15px 20px;
      position: sticky;
      top: 0;
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.1);
      animation: slideDown 0.5s ease;
    }

    @keyframes slideDown {
      from {
        transform: translateY(-100px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    .hamburger {
      width: 30px;
      height: 25px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      cursor: pointer;
      z-index: 1001;
      transition: transform 0.3s ease;
    }

    .hamburger:hover {
      transform: scale(1.1);
    }

    .hamburger span {
      width: 100%;
      height: 3px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border-radius: 3px;
      transition: all 0.3s ease;
      box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    }

    .hamburger.active span:nth-child(1) {
      transform: rotate(45deg) translateY(10px);
    }

    .hamburger.active span:nth-child(2) {
      opacity: 0;
      transform: translateX(-20px);
    }

    .hamburger.active span:nth-child(3) {
      transform: rotate(-45deg) translateY(-10px);
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;
      justify-content: center;
      animation: fadeIn 0.6s ease 0.2s both;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: scale(0.8);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    .brand-logo {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      object-fit: cover;
      border: 2px solid #00ffff;
      box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
      transition: all 0.3s ease;
      animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-5px); }
    }

    .brand-logo:hover {
      transform: scale(1.1) rotate(5deg);
      box-shadow: 0 0 25px rgba(0, 255, 255, 0.6);
    }

    .brand-name {
      font-size: 20px;
      font-weight: bold;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: gradient 3s ease infinite;
      background-size: 200% 200%;
    }

    @keyframes gradient {
      0%, 100% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
    }

    .header-icons {
      display: flex;
      gap: 15px;
      align-items: center;
    }

    .header-icon {
      width: 35px;
      height: 35px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      color: #00ffff;
      font-size: 16px;
      position: relative;
    }

    .header-icon:hover {
      background: rgba(0, 255, 255, 0.1);
      border-color: #00ffff;
      transform: translateY(-2px) rotate(5deg);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.4);
    }

    .badge {
      position: absolute;
      top: -5px;
      right: -5px;
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      color: #fff;
      font-size: 10px;
      font-weight: bold;
      padding: 2px 6px;
      border-radius: 10px;
      min-width: 18px;
      text-align: center;
      animation: bounce 1s ease infinite;
    }

    @keyframes bounce {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.2); }
    }

    /* Sidebar Menu */
    .sidebar {
      position: fixed;
      top: 0;
      left: -300px;
      width: 280px;
      height: 100vh;
      background: linear-gradient(180deg, rgba(26, 10, 46, 0.98) 0%, rgba(10, 10, 10, 0.98) 100%);
      backdrop-filter: blur(20px);
      border-right: 1px solid rgba(0, 255, 255, 0.3);
      padding: 80px 20px 20px;
      transition: left 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      z-index: 999;
      overflow-y: auto;
      box-shadow: 4px 0 24px rgba(0, 255, 255, 0.2);
    }

    .sidebar.active {
      left: 0;
    }

    .sidebar-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100vh;
      background: rgba(0, 0, 0, 0.8);
      opacity: 0;
      visibility: hidden;
      transition: all 0.4s ease;
      z-index: 998;
      backdrop-filter: blur(5px);
    }

    .sidebar-overlay.active {
      opacity: 1;
      visibility: visible;
    }

    .menu-item {
      padding: 15px 20px;
      margin-bottom: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.2);
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      color: #00ffff;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 12px;
      animation: slideInLeft 0.4s ease backwards;
      position: relative;
      overflow: hidden;
    }

    .menu-item::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.2), transparent);
      transition: left 0.5s ease;
    }

    .menu-item:hover::before {
      left: 100%;
    }

    .menu-item:nth-child(1) { animation-delay: 0.1s; }
    .menu-item:nth-child(2) { animation-delay: 0.15s; }
    .menu-item:nth-child(3) { animation-delay: 0.2s; }
    .menu-item:nth-child(4) { animation-delay: 0.25s; }
    .menu-item:nth-child(5) { animation-delay: 0.3s; }
    .menu-item:nth-child(6) { animation-delay: 0.35s; }
    .menu-item:nth-child(7) { animation-delay: 0.4s; }
    .menu-item:nth-child(8) { animation-delay: 0.45s; }

    @keyframes slideInLeft {
      from {
        transform: translateX(-50px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .menu-item:hover {
      background: rgba(0, 255, 255, 0.15);
      border-color: #00ffff;
      transform: translateX(5px) scale(1.02);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.3);
    }

    .menu-item i {
      font-size: 18px;
      width: 24px;
      text-align: center;
    }

    .menu-username {
      padding: 20px;
      margin-bottom: 20px;
      background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(168, 85, 247, 0.15));
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 16px;
      text-align: center;
      font-size: 18px;
      font-weight: bold;
      color: #00ffff;
      text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
      animation: slideInLeft 0.4s ease backwards;
      position: relative;
      overflow: hidden;
    }

    .menu-username::after {
      content: '';
      position: absolute;
      top: -50%;
      right: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
      transform: rotate(45deg);
      animation: shine 3s ease-in-out infinite;
    }

    @keyframes shine {
      0% { top: -50%; right: -50%; }
      100% { top: 150%; right: 150%; }
    }

    /* Search Bar */
    .search-container {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
      animation: fadeInUp 0.6s ease 0.3s both;
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .search-wrapper {
      position: relative;
    }

    .search-bar {
      width: 100%;
      padding: 15px 50px 15px 20px;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(10px);
      border: 2px solid rgba(0, 255, 255, 0.3);
      border-radius: 16px;
      color: #fff;
      font-size: 16px;
      transition: all 0.3s ease;
    }

    .search-bar:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 24px rgba(0, 255, 255, 0.4);
      background: rgba(255, 255, 255, 0.08);
      transform: scale(1.02);
    }

    .search-icon {
      position: absolute;
      right: 15px;
      top: 50%;
      transform: translateY(-50%);
      color: #00ffff;
      font-size: 18px;
      pointer-events: none;
      animation: pulse 2s ease-in-out infinite;
    }

    /* Cart Sidebar */
    .cart-sidebar {
      position: fixed;
      top: 0;
      right: -400px;
      width: min(400px, 90vw);
      height: 100vh;
      background: linear-gradient(180deg, rgba(26, 10, 46, 0.98) 0%, rgba(10, 10, 10, 0.98) 100%);
      backdrop-filter: blur(20px);
      border-left: 1px solid rgba(0, 255, 255, 0.3);
      z-index: 999;
      transition: right 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      overflow-y: auto;
      box-shadow: -4px 0 24px rgba(0, 255, 255, 0.2);
      padding: 20px;
    }

    .cart-sidebar.active {
      right: 0;
    }

    .cart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 15px;
      border-bottom: 1px solid rgba(0, 255, 255, 0.2);
    }

    .cart-title {
      font-size: 24px;
      color: #00ffff;
      font-weight: bold;
    }

    .cart-close {
      width: 35px;
      height: 35px;
      background: rgba(255, 0, 110, 0.2);
      border: 1px solid #ff006e;
      border-radius: 50%;
      color: #ff006e;
      font-size: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
    }

    .cart-close:hover {
      background: #ff006e;
      color: #fff;
      transform: rotate(90deg);
    }

    .cart-item {
      display: flex;
      gap: 15px;
      padding: 15px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      margin-bottom: 15px;
      border: 1px solid rgba(0, 255, 255, 0.2);
      animation: slideInRight 0.4s ease;
      transition: all 0.3s ease;
    }

    .cart-item:hover {
      background: rgba(255, 255, 255, 0.08);
      transform: translateX(-5px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.2);
    }

    .cart-item-image {
      width: 80px;
      height: 80px;
      object-fit: cover;
      border-radius: 8px;
      border: 1px solid rgba(0, 255, 255, 0.3);
    }

    .cart-item-details {
      flex: 1;
    }

    .cart-item-title {
      font-size: 16px;
      color: #00ffff;
      margin-bottom: 8px;
      font-weight: bold;
    }

    .cart-item-price {
      color: #00ff88;
      font-size: 18px;
      font-weight: bold;
    }

    .cart-item-remove {
      color: #ff006e;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 18px;
    }

    .cart-item-remove:hover {
      transform: scale(1.2) rotate(90deg);
      color: #ff4d00;
    }

    .cart-total {
      padding: 20px;
      background: rgba(0, 255, 255, 0.1);
      border-radius: 12px;
      margin: 20px 0;
      border: 1px solid rgba(0, 255, 255, 0.3);
    }

    .cart-total-label {
      font-size: 18px;
      color: #00ffff;
      margin-bottom: 10px;
    }

    .cart-total-amount {
      font-size: 32px;
      color: #00ff88;
      font-weight: bold;
      text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }

    .cart-checkout-btn {
      width: 100%;
      padding: 15px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 12px;
      color: #000;
      font-size: 18px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 20px;
    }

    .cart-checkout-btn:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.5);
    }

    .cart-checkout-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    /* Main Content */
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      animation: fadeInUp 0.6s ease 0.4s both;
    }

    .section-title {
      font-size: 28px;
      margin-bottom: 20px;
      color: #00ffff;
      text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
      animation: fadeInUp 0.6s ease;
      position: relative;
      display: inline-block;
    }

    .section-title::after {
      content: '';
      position: absolute;
      bottom: -5px;
      left: 0;
      width: 0;
      height: 3px;
      background: linear-gradient(90deg, #00ffff, #a855f7);
      animation: expandWidth 1s ease 0.5s forwards;
    }

    @keyframes expandWidth {
      to { width: 100%; }
    }

    /* Filter Slider Container */
    .filter-slider-container {
      position: relative;
      margin-bottom: 20px;
      animation: fadeInUp 0.6s ease 0.5s both;
      overflow: hidden;
    }

    .filter-slider {
      display: flex;
      gap: 10px;
      overflow-x: auto;
      scroll-behavior: smooth;
      padding: 10px 0;
      scrollbar-width: none;
      -ms-overflow-style: none;
    }

    .filter-slider::-webkit-scrollbar {
      display: none;
    }

    .filter-btn {
      padding: 10px 20px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 10px;
      color: #00ffff;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
      white-space: nowrap;
      flex-shrink: 0;
    }

    .filter-btn:hover {
      background: rgba(0, 255, 255, 0.1);
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.3);
    }

    .filter-btn.active {
      background: linear-gradient(135deg, #00ffff, #a855f7);
      color: #000;
      border-color: transparent;
    }

    /* Product Grid - 2 columns */
    .products-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 18px;
      margin-bottom: 40px;
      padding: 0;
    }

    .product-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 15px;
      transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      cursor: pointer;
      position: relative;
      overflow: hidden;
      animation: scaleIn 0.5s ease backwards;
    }

    @keyframes scaleIn {
      from {
        opacity: 0;
        transform: scale(0.8);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    .product-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(168, 85, 247, 0.1));
      opacity: 0;
      transition: opacity 0.4s ease;
      z-index: 0;
    }

    .product-card:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 15px 45px rgba(0, 255, 255, 0.4);
      border-color: rgba(0, 255, 255, 0.5);
    }

    .product-card:hover::before {
      opacity: 1;
    }

    .product-badge {
      position: absolute;
      top: 10px;
      right: 10px;
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      color: #fff;
      padding: 4px 10px;
      border-radius: 15px;
      font-size: 11px;
      font-weight: bold;
      z-index: 2;
      animation: pulse 2s ease-in-out infinite;
    }

    .product-image {
      width: 100%;
      height: 180px;
      object-fit: contain;
      border-radius: 12px;
      margin-bottom: 12px;
      border: 2px solid rgba(0, 255, 255, 0.3);
      position: relative;
      z-index: 1;
      transition: all 0.4s ease;
      background: rgba(0, 0, 0, 0.3);
    }

    .product-card:hover .product-image {
      transform: scale(1.05);
      box-shadow: 0 8px 32px rgba(0, 255, 255, 0.4);
    }

    .product-title {
      font-size: 16px;
      font-weight: bold;
      margin-bottom: 8px;
      color: #00ffff;
      position: relative;
      z-index: 1;
      transition: all 0.3s ease;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .product-card:hover .product-title {
      transform: translateX(3px);
    }

    .product-description {
      font-size: 13px;
      color: #999;
      margin-bottom: 12px;
      position: relative;
      z-index: 1;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .product-price-section {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      position: relative;
      z-index: 1;
    }

    .product-price-original {
      text-decoration: line-through;
      color: #666;
      font-size: 14px;
    }

    .product-price-discount {
      color: #00ff88;
      font-size: 20px;
      font-weight: bold;
      text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }

    .product-actions {
      display: flex;
      gap: 8px;
      position: relative;
      z-index: 1;
    }

    .btn {
      flex: 1;
      padding: 10px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 10px;
      color: #000;
      font-size: 14px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .btn::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 0;
      height: 0;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.3);
      transform: translate(-50%, -50%);
      transition: width 0.6s, height 0.6s;
    }

    .btn:active::before {
      width: 300px;
      height: 300px;
    }

    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 255, 255, 0.5);
    }

    .btn-free-download {
      flex: 1;
      padding: 10px;
      background: linear-gradient(135deg, #00ff88, #00ffff);
      border: none;
      border-radius: 10px;
      color: #000;
      font-size: 14px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .btn-free-download:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 255, 136, 0.5);
    }

    .btn-icon {
      width: 38px;
      height: 38px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.3s ease;
      color: #00ffff;
      font-size: 14px;
    }

    .btn-icon:hover {
      background: rgba(0, 255, 255, 0.2);
      border-color: #00ffff;
      transform: translateY(-2px) rotate(10deg);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.4);
    }

    .btn-icon.active {
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      border-color: transparent;
      color: #fff;
    }

    /* Modal */
    .modal {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100vh;
      background: rgba(0, 0, 0, 0.9);
      backdrop-filter: blur(10px);
      z-index: 2000;
      justify-content: center;
      align-items: center;
      padding: 20px;
      overflow-y: auto;
      animation: fadeIn 0.3s ease;
    }

    .modal.active {
      display: flex;
    }

    .modal-content {
      background: rgba(10, 10, 10, 0.98);
      backdrop-filter: blur(30px);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 24px;
      padding: 30px;
      max-width: 600px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 16px 64px rgba(0, 255, 255, 0.3);
      animation: modalSlideIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      position: relative;
    }

    /* Chat Modal Full Screen */
    #chatModal .modal-content {
      max-width: 100%;
      width: 100%;
      height: 100vh;
      max-height: 100vh;
      border-radius: 0;
      padding: 20px;
      margin: 0;
    }

    @keyframes modalSlideIn {
      from {
        opacity: 0;
        transform: translateY(-50px) scale(0.8);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    .modal-close {
      position: absolute;
      top: 20px;
      right: 20px;
      width: 40px;
      height: 40px;
      background: rgba(255, 0, 110, 0.2);
      border: 1px solid #ff006e;
      border-radius: 50%;
      color: #ff006e;
      font-size: 24px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      z-index: 10;
    }

    .modal-close:hover {
      background: #ff006e;
      color: #fff;
      transform: rotate(90deg) scale(1.1);
      box-shadow: 0 4px 16px rgba(255, 0, 110, 0.5);
    }

    .modal-image {
      width: 100%;
      height: 300px;
      object-fit: contain;
      border-radius: 16px;
      margin: 20px 0;
      border: 2px solid rgba(0, 255, 255, 0.3);
      animation: zoomIn 0.5s ease;
      background: rgba(0, 0, 0, 0.3);
    }

    @keyframes zoomIn {
      from {
        opacity: 0;
        transform: scale(0.5);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    .modal-title {
      font-size: 28px;
      margin-bottom: 15px;
      color: #00ffff;
      text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
      animation: slideInLeft 0.5s ease 0.2s both;
    }

    .modal-description {
      margin-bottom: 20px;
      color: #ccc;
      line-height: 1.8;
      animation: slideInLeft 0.5s ease 0.3s both;
    }

    /* Screenshots Section */
    .screenshots-section {
      margin: 20px 0;
      animation: slideInLeft 0.5s ease 0.4s both;
    }

    .screenshots-title {
      font-size: 18px;
      color: #00ffff;
      margin-bottom: 15px;
      font-weight: bold;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .screenshots-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
      gap: 10px;
      margin-bottom: 20px;
    }

    .screenshot-item {
      width: 100%;
      height: 120px;
      object-fit: cover;
      border-radius: 12px;
      border: 2px solid rgba(0, 255, 255, 0.3);
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(0, 0, 0, 0.3);
    }

    .screenshot-item:hover {
      transform: scale(1.05);
      border-color: #00ffff;
      box-shadow: 0 4px 20px rgba(0, 255, 255, 0.4);
    }

    .price-section {
      margin-bottom: 25px;
      padding: 20px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 16px;
      border: 1px solid rgba(0, 255, 255, 0.2);
      animation: slideInLeft 0.5s ease 0.4s both;
      position: relative;
      overflow: hidden;
    }

    .price-section::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
      animation: slideRight 2s ease infinite;
    }

    @keyframes slideRight {
      to { left: 100%; }
    }

    .price-original {
      text-decoration: line-through;
      color: #999;
      font-size: 18px;
      margin-right: 15px;
    }

    .price-discount {
      color: #00ff88;
      font-size: 32px;
      font-weight: bold;
      text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }

    .discount-badge {
      display: inline-block;
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      color: #fff;
      padding: 5px 15px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: bold;
      margin-left: 10px;
      animation: pulse 1.5s ease-in-out infinite;
    }

    .btn-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 15px;
      margin-top: 20px;
      animation: slideInUp 0.5s ease 0.5s both;
    }

    @keyframes slideInUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .btn-secondary {
      background: linear-gradient(135deg, #a855f7, #ff006e);
    }

    .btn-full {
      grid-column: 1 / -1;
    }

    .input-group {
      margin-bottom: 15px;
      animation: fadeIn 0.5s ease backwards;
    }

    .input-group:nth-child(1) { animation-delay: 0.1s; }
    .input-group:nth-child(2) { animation-delay: 0.2s; }
    .input-group:nth-child(3) { animation-delay: 0.3s; }
    .input-group:nth-child(4) { animation-delay: 0.4s; }

    .input-group label {
      display: block;
      margin-bottom: 8px;
      color: #00ffff;
      font-size: 14px;
      font-weight: 500;
    }

    .input-group input,
    .input-group textarea {
      width: 100%;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 12px;
      color: #fff;
      font-size: 16px;
      transition: all 0.3s ease;
      font-family: inherit;
    }

    .input-group textarea {
      resize: vertical;
      min-height: 100px;
    }

    .input-group input:focus,
    .input-group textarea:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
      background: rgba(255, 255, 255, 0.08);
      transform: scale(1.02);
    }

    .input-group input::placeholder,
    .input-group textarea::placeholder {
      color: #666;
    }

    .qr-image {
      width: 100%;
      max-width: 300px;
      height: auto;
      margin: 20px auto;
      display: block;
      border-radius: 16px;
      border: 2px solid #00ffff;
      box-shadow: 0 0 30px rgba(0, 255, 255, 0.4);
      animation: pulse 2s ease-in-out infinite;
    }

    .info-text {
      text-align: center;
      color: #00ffff;
      margin: 15px 0;
      font-size: 16px;
      animation: fadeIn 0.5s ease 0.3s both;
    }

    /* Coupon Section */
    .coupon-section {
      margin: 20px 0;
      padding: 20px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 16px;
      border: 1px solid rgba(0, 255, 255, 0.2);
      animation: slideInUp 0.5s ease 0.6s both;
    }

    .coupon-title {
      font-size: 18px;
      color: #00ffff;
      margin-bottom: 15px;
      font-weight: bold;
    }

    .coupon-input-wrapper {
      display: flex;
      gap: 10px;
    }

    .coupon-input {
      flex: 1;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 12px;
      color: #fff;
      font-size: 16px;
      text-transform: uppercase;
    }

    .coupon-apply-btn {
      padding: 12px 24px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 12px;
      color: #000;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      white-space: nowrap;
    }

    .coupon-apply-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.5);
    }

    .coupon-message {
      margin-top: 10px;
      padding: 10px;
      border-radius: 8px;
      font-size: 14px;
      animation: slideInUp 0.3s ease;
    }

    .coupon-message.success {
      background: rgba(0, 255, 136, 0.1);
      border: 1px solid #00ff88;
      color: #00ff88;
    }

    .coupon-message.error {
      background: rgba(255, 0, 110, 0.1);
      border: 1px solid #ff006e;
      color: #ff006e;
    }

    .applied-coupon {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: rgba(0, 255, 136, 0.1);
      border: 1px solid #00ff88;
      border-radius: 10px;
      margin-top: 10px;
      animation: slideInUp 0.3s ease;
    }

    .applied-coupon-code {
      color: #00ff88;
      font-weight: bold;
      font-size: 16px;
    }

    .applied-coupon-remove {
      color: #ff006e;
      cursor: pointer;
      font-size: 18px;
      transition: all 0.3s ease;
    }

    .applied-coupon-remove:hover {
      transform: scale(1.2);
    }

    .price-breakdown {
      margin-top: 20px;
      padding: 15px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 12px;
    }

    .price-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
      font-size: 16px;
    }

    .price-row.total {
      border-top: 1px solid rgba(0, 255, 255, 0.3);
      padding-top: 10px;
      margin-top: 10px;
      font-size: 20px;
      font-weight: bold;
      color: #00ff88;
    }

    .price-row .label {
      color: #999;
    }

    .price-row .value {
      color: #fff;
      font-weight: 500;
    }

    .price-row .discount-value {
      color: #ff006e;
    }

    /* Contact Page */
    .contact-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 30px;
      margin-bottom: 20px;
      box-shadow: 0 8px 32px rgba(0, 255, 255, 0.15);
      animation: scaleIn 0.5s ease;
    }

    .contact-item {
      margin-bottom: 20px;
      padding: 15px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      border-left: 3px solid #00ffff;
      transition: all 0.3s ease;
    }

    .contact-item:hover {
      background: rgba(255, 255, 255, 0.08);
      transform: translateX(5px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.2);
    }

    .contact-label {
      color: #00ffff;
      font-size: 14px;
      margin-bottom: 5px;
      font-weight: 500;
    }

    .contact-value {
      color: #fff;
      font-size: 16px;
      font-weight: 500;
    }

    .social-links {
      display: flex;
      gap: 15px;
      margin-top: 20px;
      flex-wrap: wrap;
    }

    .social-btn {
      padding: 12px 24px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 12px;
      color: #000;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .social-btn:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.5);
    }

    /* Accordion */
    .accordion {
      margin-bottom: 40px;
      animation: fadeInUp 0.6s ease 0.3s both;
    }

    .accordion-item {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      margin-bottom: 15px;
      overflow: hidden;
      transition: all 0.3s ease;
    }

    .accordion-item:hover {
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.2);
      transform: translateY(-2px);
    }

    .accordion-header {
      padding: 20px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: #00ffff;
      font-weight: bold;
      font-size: 16px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .accordion-header::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
      transition: left 0.5s ease;
    }

    .accordion-header:hover::before {
      left: 100%;
    }

    .accordion-header:hover {
      background: rgba(0, 255, 255, 0.1);
    }

    .accordion-icon {
      transition: transform 0.4s ease;
      font-size: 20px;
    }

    .accordion-item.active .accordion-icon {
      transform: rotate(180deg);
      color: #a855f7;
    }

    .accordion-content {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      padding: 0 20px;
    }

    .accordion-item.active .accordion-content {
      max-height: 1000px;
      padding: 0 20px 20px;
    }

    .accordion-text {
      color: #ccc;
      line-height: 1.8;
      animation: fadeIn 0.5s ease;
    }

    /* Empty State */
    .empty-state {
      text-align: center;
      padding: 80px 20px;
      color: #999;
      animation: fadeIn 0.5s ease;
    }

    .empty-icon {
      font-size: 80px;
      margin-bottom: 20px;
      opacity: 0.5;
      animation: float 3s ease-in-out infinite;
    }

    .empty-title {
      font-size: 24px;
      color: #00ffff;
      margin-bottom: 10px;
    }

    .empty-text {
      font-size: 16px;
      line-height: 1.6;
    }

    /* Pagination */
    .pagination {
      display: flex;
      justify-content: center;
      gap: 10px;
      margin: 40px 0;
      animation: fadeInUp 0.6s ease;
    }

    .pagination-btn {
      padding: 10px 20px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 10px;
      color: #00ffff;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
    }

    .pagination-btn:hover {
      background: rgba(0, 255, 255, 0.1);
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.3);
    }

    .pagination-btn.active {
      background: linear-gradient(135deg, #00ffff, #a855f7);
      color: #000;
      border-color: transparent;
    }

    .pagination-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
      transform: none;
    }

    /* Stats Cards */
    .stats-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
      animation: fadeInUp 0.6s ease 0.2s both;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      text-align: center;
      transition: all 0.4s ease;
      position: relative;
      overflow: hidden;
    }

    .stat-card::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent, rgba(0, 255, 255, 0.1), transparent);
      transform: rotate(45deg);
      transition: all 0.6s ease;
    }

    .stat-card:hover::before {
      top: 150%;
      right: 150%;
    }

    .stat-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 12px 40px rgba(0, 255, 255, 0.3);
      border-color: rgba(0, 255, 255, 0.5);
    }

    .stat-icon {
      font-size: 36px;
      margin-bottom: 10px;
      color: #00ffff;
      animation: bounce 2s ease-in-out infinite;
    }

    .stat-value {
      font-size: 28px;
      font-weight: bold;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 5px;
    }

    .stat-label {
      color: #999;
      font-size: 14px;
    }

    /* Order History Card */
    .order-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 20px;
      transition: all 0.3s ease;
      animation: slideInLeft 0.5s ease backwards;
    }

    .order-card:hover {
      transform: translateX(5px);
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.3);
      border-color: rgba(0, 255, 255, 0.5);
    }

    .order-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding-bottom: 15px;
      border-bottom: 1px solid rgba(0, 255, 255, 0.2);
    }

    .order-id {
      color: #a855f7;
      font-weight: bold;
      font-size: 14px;
    }

    .order-date {
      color: #999;
      font-size: 12px;
    }

    .order-status {
      display: inline-block;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      animation: pulse 2s ease-in-out infinite;
    }

    .order-status.pending {
      background: rgba(255, 165, 0, 0.2);
      color: #ffa500;
      border: 1px solid #ffa500;
    }

    .order-status.confirmed {
      background: rgba(0, 255, 136, 0.2);
      color: #00ff88;
      border: 1px solid #00ff88;
    }

    .order-status.processing {
      background: rgba(0, 255, 255, 0.2);
      color: #00ffff;
      border: 1px solid #00ffff;
    }

    .order-body {
      display: flex;
      gap: 15px;
      margin-bottom: 15px;
    }

    .order-image {
      width: 80px;
      height: 80px;
      object-fit: cover;
      border-radius: 10px;
      border: 1px solid rgba(0, 255, 255, 0.3);
    }

    .order-details {
      flex: 1;
    }

    .order-product-title {
      font-size: 16px;
      color: #00ffff;
      margin-bottom: 8px;
      font-weight: bold;
    }

    .order-price {
      color: #00ff88;
      font-size: 18px;
      font-weight: bold;
    }

    .order-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid rgba(0, 255, 255, 0.2);
      flex-wrap: wrap;
      gap: 10px;
    }

    .order-utr {
      font-size: 12px;
      color: #999;
    }

    .order-utr strong {
      color: #00ffff;
    }

    .download-btn {
      padding: 8px 16px;
      background: linear-gradient(135deg, #00ff88, #00ffff);
      border: none;
      border-radius: 8px;
      color: #000;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 12px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .download-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 255, 136, 0.5);
    }

    .download-btn i {
      font-size: 14px;
    }

    /* Confirm Dialog */
    .confirm-dialog {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(10, 10, 10, 0.98);
      backdrop-filter: blur(30px);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 20px;
      padding: 30px;
      z-index: 10002;
      display: none;
      animation: scaleIn 0.3s ease;
      box-shadow: 0 16px 64px rgba(0, 255, 255, 0.4);
      min-width: 320px;
    }

    .confirm-dialog.active {
      display: block;
    }

    .confirm-dialog-title {
      font-size: 22px;
      color: #00ffff;
      margin-bottom: 15px;
      font-weight: bold;
      text-align: center;
    }

    .confirm-dialog-message {
      color: #ccc;
      margin-bottom: 25px;
      text-align: center;
      line-height: 1.6;
    }

    .confirm-dialog-buttons {
      display: flex;
      gap: 10px;
    }

    .confirm-btn {
      flex: 1;
      padding: 12px;
      border: none;
      border-radius: 10px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 14px;
    }

    .confirm-btn.yes {
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      color: #fff;
    }

    .confirm-btn.no {
      background: rgba(255, 255, 255, 0.1);
      color: #00ffff;
      border: 1px solid rgba(0, 255, 255, 0.3);
    }

    .confirm-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.4);
    }

    /* Chat Box Styles */
    .chat-container {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 180px);
      max-height: none;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid rgba(0, 255, 255, 0.2);
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .chat-message {
      display: flex;
      gap: 10px;
      animation: slideInLeft 0.3s ease;
    }

    .chat-message.user {
      flex-direction: row-reverse;
      animation: slideInRight 0.3s ease;
    }

    .chat-message-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #000;
      font-weight: bold;
      flex-shrink: 0;
    }

    .chat-message.user .chat-message-avatar {
      background: linear-gradient(135deg, #a855f7, #ff006e);
    }

    .chat-message-content {
      max-width: 70%;
      padding: 12px 16px;
      border-radius: 16px;
      background: rgba(0, 255, 255, 0.1);
      border: 1px solid rgba(0, 255, 255, 0.3);
      color: #fff;
      line-height: 1.5;
    }

    .chat-message.user .chat-message-content {
      background: rgba(168, 85, 247, 0.1);
      border-color: rgba(168, 85, 247, 0.3);
    }

    .chat-message-time {
      font-size: 11px;
      color: #999;
      margin-top: 5px;
    }

    .chat-input-container {
      display: flex;
      gap: 10px;
      padding: 15px;
      background: rgba(255, 255, 255, 0.05);
      border-top: 1px solid rgba(0, 255, 255, 0.2);
    }

    .chat-input {
      flex: 1;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 12px;
      color: #fff;
      font-size: 14px;
      transition: all 0.3s ease;
    }

    .chat-input:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
      background: rgba(255, 255, 255, 0.08);
    }

    .chat-send-btn {
      width: 45px;
      height: 45px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 12px;
      color: #000;
      font-size: 18px;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .chat-send-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.5);
    }

    .chat-send-btn:active {
      transform: scale(0.95);
    }

    .chat-empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #999;
      gap: 10px;
    }

    .chat-empty-icon {
      font-size: 60px;
      opacity: 0.5;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
      width: 10px;
      height: 10px;
    }

    ::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, 0.05);
    }

    ::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: linear-gradient(135deg, #a855f7, #00ffff);
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .products-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
      }

      /* Chat Modal Mobile Full Screen */
      #chatModal .modal-content {
        padding: 15px;
        height: 100vh;
        border-radius: 0;
      }

      .chat-container {
        height: calc(100vh - 150px);
      }

      .btn-group {
        grid-template-columns: 1fr;
      }

      .modal-content {
        padding: 20px;
        margin: 10px;
      }

      .brand-name {
        font-size: 16px;
      }

      .section-title {
        font-size: 24px;
      }

      .header-icons {
        gap: 10px;
      }

      .stats-container {
        grid-template-columns: 1fr;
      }

      .coupon-input-wrapper {
        flex-direction: column;
      }

      .order-body {
        flex-direction: column;
      }

      .order-footer {
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;
      }

      .product-image {
        height: 150px;
      }

      .product-title {
        font-size: 14px;
      }

      .product-description {
        font-size: 12px;
      }

      .screenshots-grid {
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
      }

      .screenshot-item {
        height: 100px;
      }

      .chat-message-content {
        max-width: 85%;
      }
    }

    @media (min-width: 769px) and (max-width: 1024px) {
      .products-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    /* Animations for page transitions */
    @keyframes pageTransition {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .page-transition {
      animation: pageTransition 0.5s ease;
    }

    /* Shimmer Loading Effect */
    .shimmer {
      background: linear-gradient(90deg, 
        rgba(255, 255, 255, 0.05) 0%, 
        rgba(255, 255, 255, 0.1) 50%, 
        rgba(255, 255, 255, 0.05) 100%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
    }

    @keyframes shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }

    .shimmer-card {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 20px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .shimmer-image {
      width: 100%;
      height: 220px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      margin-bottom: 15px;
    }

    .shimmer-text {
      height: 20px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      margin-bottom: 10px;
    }

    .shimmer-text.short {
      width: 60%;
    }

    /* Floating Action Button */
    .fab {
      position: fixed;
      bottom: 30px;
      right: 30px;
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border-radius: 50%;
      display: none;
      align-items: center;
      justify-content: center;
      color: #000;
      font-size: 24px;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.5);
      transition: all 0.3s ease;
      z-index: 100;
      animation: fadeIn 0.3s ease;
    }

    .fab:hover {
      transform: scale(1.1) rotate(10deg);
      box-shadow: 0 12px 32px rgba(0, 255, 255, 0.7);
    }

    .fab.show {
      display: flex;
    }

    /* Success Animation */
    @keyframes successPulse {
      0%, 100% {
        transform: scale(1);
        opacity: 1;
      }
      50% {
        transform: scale(1.1);
        opacity: 0.8;
      }
    }

    .success-animation {
      animation: successPulse 0.6s ease;
    }

    /* Particle Background Effect */
    .particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    }

    .particle {
      position: absolute;
      width: 4px;
      height: 4px;
      background: #00ffff;
      border-radius: 50%;
      opacity: 0.3;
      animation: particleFloat 20s linear infinite;
    }

    @keyframes particleFloat {
      0% {
        transform: translateY(100vh) translateX(0);
        opacity: 0;
      }
      10% {
        opacity: 0.3;
      }
      90% {
        opacity: 0.3;
      }
      100% {
        transform: translateY(-100vh) translateX(100px);
        opacity: 0;
      }
    }
    /* Games / Spin Wheel */
    .games-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 15px;
      margin-top: 20px;
    }
    .game-card {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.2);
      border-radius: 16px;
      padding: 20px 15px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s;
    }
    .game-card:hover {
      background: rgba(0, 255, 255, 0.1);
      transform: translateY(-4px);
      border-color: #00ffff;
    }
    .game-card-icon { font-size: 34px; margin-bottom: 10px; }
    .game-card-title { font-weight: 600; margin-bottom: 4px; font-size: 14px; }
    .game-card-desc { font-size: 11px; color: rgba(255, 255, 255, 0.55); }
    .game-card.coming-soon { opacity: 0.5; cursor: not-allowed; }
    .game-card.coming-soon:hover {
      transform: none;
      border-color: rgba(0, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.05);
    }
    .coming-soon-badge {
      display: inline-block;
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 0.5px;
      padding: 3px 8px;
      border-radius: 10px;
      margin-top: 8px;
    }
    .games-back-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.2);
      color: #fff;
      padding: 8px 14px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 13px;
      margin-bottom: 15px;
    }
    .games-back-btn:hover { background: rgba(0, 255, 255, 0.1); }
    .wheel-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 5px;
    }
    .wheel-pointer {
      width: 0; height: 0;
      border-left: 14px solid transparent;
      border-right: 14px solid transparent;
      border-top: 24px solid #00ffff;
      margin-bottom: -6px;
      z-index: 2;
      filter: drop-shadow(0 0 6px rgba(0, 255, 255, 0.8));
    }
    .wheel-outer {
      position: relative;
      width: 260px;
      height: 260px;
      border-radius: 50%;
      padding: 7px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      box-shadow: 0 0 30px rgba(0, 255, 255, 0.35);
    }
    .wheel {
      position: relative;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      background: #1a0a2e;
      transition: transform 4.5s cubic-bezier(0.12, 0.85, 0.2, 1);
    }
    .wheel-segment-label {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 90px;
      margin-left: -45px;
      text-align: center;
      font-size: 10.5px;
      font-weight: 700;
      color: #fff;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
      transform-origin: center;
    }
    .wheel-center {
      position: absolute;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      width: 46px; height: 46px;
      border-radius: 50%;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      display: flex; align-items: center; justify-content: center;
      font-size: 18px;
      z-index: 3;
      box-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
    }
    .spin-btn { margin-top: 22px; min-width: 160px; }
    .spin-status {
      margin-top: 12px;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.65);
      text-align: center;
      min-height: 18px;
    }
    .spin-result {
      margin-top: 15px;
      text-align: center;
      padding: 15px;
      border-radius: 12px;
      display: none;
    }
    .spin-result.win {
      display: block;
      background: linear-gradient(135deg, rgba(0, 255, 136, 0.15), rgba(0, 255, 255, 0.15));
      border: 1px solid rgba(0, 255, 136, 0.4);
    }
    .spin-result.lose {
      display: block;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .spin-coupon-code {
      font-size: 22px;
      font-weight: 700;
      letter-spacing: 2px;
      color: #00ff88;
      margin: 8px 0;
    }
    .scratch-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: 5px;
    }
    .scratch-card-frame {
      position: relative;
      width: 280px;
      height: 160px;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
      border: 2px solid rgba(0, 255, 255, 0.4);
    }
    .scratch-reveal {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(168, 85, 247, 0.15));
      text-align: center;
      padding: 10px;
    }
    #scratchCanvas {
      position: absolute;
      inset: 0;
      cursor: pointer;
      touch-action: none;
    }
  </style>
</head>
<body>
  <!-- Loading Overlay -->
  <div class="loading-overlay" id="loadingOverlay">
    <div class="loading-content">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading...</div>
    </div>
  </div>

  <!-- Notification Toast -->
  <div class="notification-toast" id="notificationToast"></div>

  <!-- Confirm Dialog -->
  <div class="confirm-dialog" id="confirmDialog">
    <div class="confirm-dialog-title" id="confirmTitle">Confirm Action</div>
    <div class="confirm-dialog-message" id="confirmMessage">Are you sure?</div>
    <div class="confirm-dialog-buttons">
      <button class="confirm-btn no" id="confirmNo">Cancel</button>
      <button class="confirm-btn yes" id="confirmYes">Confirm</button>
    </div>
  </div>

  <!-- Header -->
  <div class="header">
    <div class="hamburger" id="hamburger" onclick="toggleMenu()">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <div class="brand-section">
      <img id="headerLogo" class="brand-logo" src="" alt="Logo" style="display:none;">
      <div id="headerBrandName" class="brand-name">Premium Shop</div>
    </div>
    <div class="header-icons">
      <div class="header-icon" onclick="toggleCart()" title="Shopping Cart">
        <i class="fas fa-shopping-cart"></i>
        <span class="badge" id="cartBadge" style="display: none;">0</span>
      </div>
    </div>
  </div>

  <!-- Sidebar Menu -->
  <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleMenu()"></div>
  <div class="sidebar" id="sidebar">
    <div id="menuContent"></div>
  </div>

  <!-- Cart Sidebar -->
  <div class="cart-sidebar" id="cartSidebar">
    <div class="cart-header">
      <div class="cart-title"><i class="fas fa-shopping-cart"></i> Cart</div>
      <div class="cart-close" onclick="toggleCart()">×</div>
    </div>
    <div id="cartItems"></div>
    <div class="cart-total" id="cartTotal" style="display: none;">
      <div class="cart-total-label">Total Amount:</div>
      <div class="cart-total-amount" id="cartTotalAmount">$0</div>
    </div>
    <button class="cart-checkout-btn" id="cartCheckoutBtn" onclick="checkoutCart()" disabled>
      <i class="fas fa-credit-card"></i> Proceed to Checkout
    </button>
  </div>

  <!-- Search Bar -->
  <div class="search-container">
    <div class="search-wrapper">
      <input type="text" class="search-bar" id="searchBar" placeholder="🔍 Search products..." oninput="searchProducts()">
      <span class="search-icon"><i class="fas fa-search"></i></span>
    </div>
  </div>

  <!-- Main Container -->
  <div class="container">
    <div id="mainContent">
      <!-- Filter Slider Container -->
      <div class="filter-slider-container" id="filterSliderContainer" style="display: none;">
        <div class="filter-slider" id="filterSlider">
          <button class="filter-btn active" data-filter="all" onclick="filterProducts('all')">
  <i class="fas fa-th"></i> All Products
</button>
<button class="filter-btn" data-filter="premium" onclick="filterProducts('premium')">
  <i class="fas fa-star"></i> Premium Product
</button>
<button class="filter-btn" data-filter="budget" onclick="filterProducts('budget')">
  <i class="fas fa-fire"></i> Budget Friendly
</button>
<button class="filter-btn" data-filter="free" onclick="filterProducts('free')">
  <i class="fas fa-tag"></i> Free Product
</button>
        </div>
      </div>

      <h2 class="section-title"><i class="fas fa-shopping-bag"></i> Products</h2>
      <div id="productsGrid" class="products-grid"></div>
      
      <!-- Pagination -->
      <div class="pagination" id="pagination" style="display: none;"></div>
    </div>
  </div>

  <!-- Product Detail Modal -->
  <div id="productModal" class="modal">
    <div class="modal-content">
      <span class="modal-close" onclick="closeModal('productModal')">×</span>
      <img id="modalImage" class="modal-image" src="" alt="Product">
      <h2 id="modalTitle" class="modal-title"></h2>
      <p id="modalDescription" class="modal-description"></p>
      
      <!-- Screenshots Section -->
      <div class="screenshots-section" id="screenshotsSection" style="display: none;">
        <div class="screenshots-title">
          <i class="fas fa-images"></i> Product Screenshots
        </div>
        <div class="screenshots-grid" id="screenshotsGrid"></div>
      </div>

      <div class="price-section">
        <span id="modalPriceOriginal" class="price-original"></span>
        <span id="modalPriceDiscount" class="price-discount"></span>
        <span id="modalDiscountBadge" class="discount-badge" style="display: none;"></span>
      </div>
      <div class="btn-group" id="modalButtonGroup">
        <!-- Buttons will be dynamically added based on price -->
      </div>
    </div>
  </div>

  <!-- Checkout Modal -->
  <div id="checkoutModal" class="modal">
    <div class="modal-content">
      <span class="modal-close" onclick="closeModal('checkoutModal')">×</span>
      <h2 class="modal-title"><i class="fas fa-credit-card"></i> Checkout</h2>
      
      <div id="checkoutItems"></div>

      <!-- Coupon Section -->
      <div class="coupon-section">
        <div class="coupon-title"><i class="fas fa-ticket-alt"></i> Have a Coupon Code?</div>
        <div id="appliedCouponDisplay" style="display: none;"></div>
        <div id="couponInputSection">
          <div class="coupon-input-wrapper">
            <input type="text" class="coupon-input" id="couponInput" placeholder="Enter coupon code" maxlength="20">
            <button class="coupon-apply-btn" onclick="applyCoupon()">
              <i class="fas fa-check"></i> Apply
            </button>
          </div>
          <div id="couponMessage" style="display: none;"></div>
        </div>
      </div>

      <!-- Price Breakdown -->
      <div class="price-breakdown">
        <div class="price-row">
          <span class="label">Subtotal:</span>
          <span class="value" id="checkoutSubtotal">$0</span>
        </div>
        <div class="price-row" id="discountRow" style="display: none;">
          <span class="label">Discount:</span>
          <span class="discount-value" id="checkoutDiscount">+$0</span>
        </div>
        <div class="price-row total">
          <span class="label">Total:</span>
          <span class="value" id="checkoutTotal">$0</span>
        </div>
      </div>

      <div class="btn-group">
        <button class="btn btn-secondary" onclick="closeModal('checkoutModal')">
          <i class="fas fa-arrow-left"></i> Back
        </button>
        <button class="btn" onclick="proceedToPayment()">
          <i class="fas fa-arrow-right"></i> Proceed to Pay
        </button>
      </div>
    </div>
  </div>

  <!-- Payment Modal (QR) -->
  <div id="paymentModal" class="modal">
    <div class="modal-content">
      <span class="modal-close" onclick="closeModal('paymentModal')">×</span>
      <h2 class="modal-title"><i class="fas fa-qrcode"></i> Complete Payment</h2>
      
      <div class="price-section">
        <div style="text-align: center;">
          <div style="color: #999; margin-bottom: 10px;">Total Amount to Pay</div>
          <span class="price-discount" id="paymentAmount">$0</span>
        </div>
      </div>

      <img class="qr-image" src="https://i.ibb.co/RTNBtWmc/file-000000004df8724699e53cff0d1f183c.png" alt="QR Code">
      <p class="info-text">
        <i class="fas fa-info-circle"></i> Scan the QR code and complete payment. Enter your payment details below to confirm your order.
      </p>
      
      <div class="input-group">
        <label><i class="fas fa-dollar-sign"></i> Enter Your Amount</label>
        <input type="number" id="userAmount" placeholder="Enter amount you paid" min="1" required>
        <small style="color: #999; font-size: 12px; margin-top: 5px; display: block;">
          Enter the exact amount you paid via UPI/Bank Transfer
        </small>
      </div>

      <div class="input-group">
        <label><i class="fas fa-receipt"></i> UTR ID / Transaction ID</label>
        <input type="text" id="utrId" placeholder="Enter 10-16 character UTR ID" maxlength="16" required>
        <small style="color: #999; font-size: 12px; margin-top: 5px; display: block;">
          UTR ID is found in your payment confirmation message/screenshot
        </small>
      </div>
      
      <div class="btn-group">
        <button class="btn btn-secondary" onclick="closeModal('paymentModal')">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button class="btn" onclick="confirmPurchase()">
          <i class="fas fa-check"></i> Confirm Order
        </button>
      </div>
    </div>
  </div>

  <!-- Auth Modal -->
  <div id="authModal" class="modal">
    <div class="modal-content">
      <span class="modal-close" onclick="closeModal('authModal')">×</span>
      <h2 class="modal-title" id="authTitle"><i class="fas fa-sign-in-alt"></i> Login</h2>
      
      <div id="loginForm">
        <div class="input-group">
          <label><i class="fas fa-envelope"></i> Email</label>
          <input type="email" id="loginEmail" placeholder="your@email.com" autocomplete="email">
        </div>
        <div class="input-group">
          <label><i class="fas fa-lock"></i> Password</label>
          <input type="password" id="loginPassword" placeholder="Enter password" autocomplete="current-password">
        </div>
        <button class="btn btn-full" onclick="loginUser()">
          <i class="fas fa-sign-in-alt"></i> Login
        </button>
        <p style="text-align: center; margin-top: 15px; color: #999;">
          Don't have an account? <span style="color: #00ffff; cursor: pointer; font-weight: bold;" onclick="switchToSignup()">Sign up</span>
        </p>
      </div>

      <div id="signupForm" style="display: none;">
        <div class="input-group">
          <label><i class="fas fa-user"></i> Full Name</label>
          <input type="text" id="signupName" placeholder="Your name" autocomplete="name">
        </div>
        <div class="input-group">
          <label><i class="fas fa-envelope"></i> Email</label>
          <input type="email" id="signupEmail" placeholder="your@email.com" autocomplete="email">
        </div>
        <div class="input-group">
          <label><i class="fas fa-lock"></i> Password (min 6 characters)</label>
          <input type="password" id="signupPassword" placeholder="Create password" autocomplete="new-password">
        </div>
        <button class="btn btn-full" onclick="signupUser()">
          <i class="fas fa-user-plus"></i> Create Account
        </button>
        <p style="text-align: center; margin-top: 15px; color: #999;">
          Already have an account? <span style="color: #00ffff; cursor: pointer; font-weight: bold;" onclick="switchToLogin()">Login</span>
        </p>
      </div>
    </div>
  </div>

  <!-- Admin Support Chat Modal -->
  <div id="chatModal" class="modal">
    <div class="modal-content">
      <span class="modal-close" onclick="closeModal('chatModal')">×</span>
      <h2 class="modal-title"><i class="fas fa-headset"></i> Admin Support</h2>
      
      <div class="chat-container">
        <div class="chat-messages" id="chatMessages">
          <div class="chat-empty-state">
            <div class="chat-empty-icon">💬</div>
            <div>Start a conversation with admin</div>
          </div>
        </div>
        <div class="chat-input-container">
          <input type="text" class="chat-input" id="chatInput" placeholder="Type your message..." maxlength="500">
          <button class="chat-send-btn" onclick="sendMessage()">
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Games / Spin Wheel Modal -->
  <div id="gamesModal" class="modal">
    <div class="modal-content">
      <span class="modal-close" onclick="closeModal('gamesModal')">×</span>
      <h2 class="modal-title"><i class="fas fa-gamepad"></i> Play Games, Earn Coupons</h2>

      <div id="gamesGridView">
        <p style="color: rgba(255,255,255,0.6); font-size: 13px; margin-top: 5px;">
          Play a game for a chance to win a real discount coupon!
        </p>
        <div style="background: rgba(255, 165, 0, 0.12); border: 1px solid rgba(255, 165, 0, 0.4); border-radius: 10px; padding: 10px 14px; font-size: 12px; color: #ffcc80; margin-top: 10px;">
          <i class="fas fa-info-circle"></i> Choose wisely — you can only play <strong>one</strong> game per day, Spin the Wheel <strong>or</strong> Scratch Card, not both.
        </div>
        <div id="gamesAlreadyPlayedBanner" style="display: none; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 10px 14px; font-size: 12px; color: rgba(255,255,255,0.7); margin-top: 10px;">
          <i class="fas fa-clock"></i> <span id="gamesAlreadyPlayedText">You've already played today.</span>
        </div>
        <div class="games-grid">
          <div class="game-card" id="spinGameCard" onclick="openSpinWheel()">
            <div class="game-card-icon">🎡</div>
            <div class="game-card-title">Spin & Win</div>
            <div class="game-card-desc">Spin the wheel for a coupon</div>
          </div>
          <div class="game-card" id="scratchGameCard" onclick="openScratchCard()">
            <div class="game-card-icon">🎟️</div>
            <div class="game-card-title">Scratch & Win</div>
            <div class="game-card-desc">Scratch to reveal a coupon</div>
          </div>
          <div class="game-card coming-soon">
            <div class="game-card-icon">🧠</div>
            <div class="game-card-title">Trivia Challenge</div>
            <div class="game-card-desc">Answer & earn rewards</div>
            <div class="coming-soon-badge">COMING SOON</div>
          </div>
        </div>
      </div>

      <div id="scratchCardView" style="display: none;">
        <button class="games-back-btn" onclick="backToGamesGrid()"><i class="fas fa-arrow-left"></i> Back</button>
        <div class="scratch-wrapper">
          <div class="scratch-card-frame">
            <div class="scratch-reveal" id="scratchReveal"></div>
            <canvas id="scratchCanvas" width="280" height="160"></canvas>
          </div>
          <div class="spin-status" id="scratchStatus">Scratch the card to reveal your prize!</div>
          <div class="spin-result" id="scratchResult"></div>
        </div>
      </div>

      <div id="spinWheelView" style="display: none;">
        <button class="games-back-btn" onclick="backToGamesGrid()"><i class="fas fa-arrow-left"></i> Back</button>

        <div class="wheel-wrapper">
          <div class="wheel-pointer"></div>
          <div class="wheel-outer">
            <div class="wheel" id="spinWheel">
              <div class="wheel-center">🎁</div>
            </div>
          </div>
          <button class="btn btn-primary spin-btn" id="spinBtn" onclick="spinWheel()">
            <i class="fas fa-sync"></i> Spin the Wheel
          </button>
          <div class="spin-status" id="spinStatus"></div>

          <div class="spin-result" id="spinResult"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Screenshot Preview Modal -->
  <div id="screenshotModal" class="modal">
    <div class="modal-content">
      <span class="modal-close" onclick="closeModal('screenshotModal')">×</span>
      <img id="screenshotPreview" class="modal-image" src="" alt="Screenshot" style="height: auto; max-height: 70vh;">
    </div>
  </div>

  <!-- Floating Action Button -->
  <div class="fab" id="fab" onclick="scrollToTop()">
    <i class="fas fa-arrow-up"></i>
  </div>

  <!-- Firebase SDK -->
  <script type="module">
    import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js';
    import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged, updateProfile } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js';
    import { getDatabase, ref, set, get, push, onValue, remove, update, query, orderByChild, limitToLast } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-database.js';

    const firebaseConfig = {
    apiKey: "AIzaSyBY19bfyTxQKV9qp_mGAPhJOVpUgy-v6R8",
  authDomain: "cipher-pro-store.firebaseapp.com",
  databaseURL: "https://cipher-pro-store-default-rtdb.firebaseio.com",
  projectId: "cipher-pro-store",
  storageBucket: "cipher-pro-store.firebasestorage.app",
  messagingSenderId: "445639151152",
  appId: "1:445639151152:web:93cbca2068849284cd67f5",
  measurementId: "G-BZRH898NCH"
};

    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const db = getDatabase(app);

    window.auth = auth;
    window.db = db;
    window.dbRef = ref;
    window.dbSet = set;
    window.dbGet = get;
    window.dbPush = push;
    window.dbOnValue = onValue;
    window.dbRemove = remove;
    window.dbUpdate = update;
    window.dbQuery = query;
    window.dbOrderByChild = orderByChild;
    window.dbLimitToLast = limitToLast;
    window.authCreateUser = createUserWithEmailAndPassword;
    window.authSignIn = signInWithEmailAndPassword;
    window.authSignOut = signOut;
    window.authUpdateProfile = updateProfile;

    window.currentUser = null;
    window.allProducts = [];
    window.currentProduct = null;
    window.cart = [];
    window.appliedCoupon = null;
    window.currentFilter = 'all';
    window.confirmCallback = null;

    // Check auth state
    onAuthStateChanged(auth, (user) => {
      window.currentUser = user;
      updateMenu();
      loadProducts();
      loadCartFromStorage();
      if (user) {
        loadChatMessages();
      }
    });

    // Load brand settings
    async function loadBrandSettings() {
      try {
        const snapshot = await get(ref(db, 'meta/brand'));
        if (snapshot.exists()) {
          const data = snapshot.val();
          if (data.logoUrl) {
            document.getElementById('headerLogo').src = data.logoUrl;
            document.getElementById('headerLogo').style.display = 'block';
          }
          if (data.name) {
            document.getElementById('headerBrandName').textContent = data.name;
          }
        }
      } catch (error) {
        console.error('Error loading brand:', error);
      }
    }

    loadBrandSettings();

    // Real-time listeners for products
    onValue(ref(db, 'products'), (snapshot) => {
      if (snapshot.exists()) {
        window.allProducts = Object.entries(snapshot.val()).map(([id, product]) => ({
          id,
          ...product
        }));
        displayProducts(window.allProducts);
      }
    });
  </script>

  <script>
    // Global variables
    let isLoading = false;
    const ITEMS_PER_PAGE = 12;
    let currentPage = 1;

    // Show loading overlay
    function showLoading(text = 'Loading...') {
      const overlay = document.getElementById('loadingOverlay');
      overlay.querySelector('.loading-text').textContent = text;
      overlay.classList.add('active');
      isLoading = true;
    }

    // Hide loading overlay
    function hideLoading() {
      document.getElementById('loadingOverlay').classList.remove('active');
      isLoading = false;
    }

    // Show notification
    function showNotification(message, type = 'success') {
      const toast = document.getElementById('notificationToast');
      toast.textContent = message;
      toast.className = `notification-toast show ${type}`;
      
      setTimeout(() => {
        toast.classList.remove('show');
      }, 3000);
    }

    // Show confirm dialog
    function showConfirmDialog(title, message, callback) {
      document.getElementById('confirmTitle').textContent = title;
      document.getElementById('confirmMessage').textContent = message;
      document.getElementById('confirmDialog').classList.add('active');
      window.confirmCallback = callback;
    }

    // Hide confirm dialog
    function hideConfirmDialog() {
      document.getElementById('confirmDialog').classList.remove('active');
      window.confirmCallback = null;
    }

    // Confirm dialog event listeners
    document.getElementById('confirmYes').addEventListener('click', function() {
      if (window.confirmCallback) {
        window.confirmCallback(true);
      }
      hideConfirmDialog();
    });

    document.getElementById('confirmNo').addEventListener('click', function() {
      if (window.confirmCallback) {
        window.confirmCallback(false);
      }
      hideConfirmDialog();
    });

    // Toggle menu
    function toggleMenu() {
      document.getElementById('hamburger').classList.toggle('active');
      document.getElementById('sidebar').classList.toggle('active');
      document.getElementById('sidebarOverlay').classList.toggle('active');
      document.body.style.overflow = document.getElementById('sidebar').classList.contains('active') ? 'hidden' : '';
    }

    // Update menu based on auth state
    function updateMenu() {
      const menuContent = document.getElementById('menuContent');
      const user = window.currentUser;

      if (user) {
        menuContent.innerHTML = `
          <div class="menu-username">
            <i class="fas fa-user-circle"></i><br>
            ${escapeHtml(user.displayName || user.email)}
          </div>
          <div class="menu-item" onclick="showProducts()">
            <i class="fas fa-shopping-bag"></i> Products
          </div>
          <div class="menu-item" onclick="showPurchaseHistory()">
            <i class="fas fa-history"></i> Purchase History
          </div>
          <div class="menu-item" onclick="showBookmarks()">
            <i class="fas fa-bookmark"></i> Bookmarks
          </div>
          <div class="menu-item" onclick="showAdminSupport()">
            <i class="fas fa-headset"></i> Admin Support
          </div>
          <div class="menu-item" onclick="openGamesModal()">
            <i class="fas fa-gamepad"></i> Get Coupon by Playing Games
          </div>
          <div class="menu-item" onclick="showContact()">
            <i class="fas fa-phone"></i> Contact Us
          </div>
          <div class="menu-item" onclick="logoutUser()">
            <i class="fas fa-sign-out-alt"></i> Logout
          </div>
        `;
      } else {
        menuContent.innerHTML = `
          <div class="menu-item" onclick="showProducts()">
            <i class="fas fa-shopping-bag"></i> Products
          </div>
          <div class="menu-item" onclick="requireLogin('view bookmarks')">
            <i class="fas fa-bookmark"></i> Bookmarks
          </div>
          <div class="menu-item" onclick="requireLogin('contact admin support')">
            <i class="fas fa-headset"></i> Admin Support
          </div>
          <div class="menu-item" onclick="requireLogin('play games and earn coupons')">
            <i class="fas fa-gamepad"></i> Get Coupon by Playing Games
          </div>
          <div class="menu-item" onclick="showContact()">
            <i class="fas fa-phone"></i> Contact Us
          </div>
          <div class="menu-item" onclick="showAuth()">
            <i class="fas fa-sign-in-alt"></i> Login / Signup
          </div>
        `;
      }
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    // Format currency
    function formatCurrency(amount) {
      return '$' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      });
    }

    // Calculate discount percentage
    function calculateDiscountPercent(original, discounted) {
      const discount = ((original - discounted) / original) * 100;
      return Math.round(discount);
    }

    // Load products
    async function loadProducts() {
      try {
        if (window.allProducts.length === 0) {
          showLoading('Loading products...');
          const snapshot = await window.dbGet(window.dbRef(window.db, 'products'));
          hideLoading();
          
          if (snapshot.exists()) {
            window.allProducts = Object.entries(snapshot.val()).map(([id, product]) => ({
              id,
              ...product
            })).sort((a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0));
            
            displayProducts(window.allProducts);
          } else {
            displayEmptyState('products');
          }
        } else {
          displayProducts(window.allProducts);
        }
      } catch (error) {
        hideLoading();
        console.error('Error loading products:', error);
        showNotification('Failed to load products', 'error');
      }
    }

    // Display products
    function displayProducts(products) {
      const grid = document.getElementById('productsGrid');
      grid.innerHTML = '';

      if (products.length === 0) {
        displayEmptyState('products');
        document.getElementById('filterSliderContainer').style.display = 'none';
        return;
      }

      // Pagination
      const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
      const endIndex = startIndex + ITEMS_PER_PAGE;
      const paginatedProducts = products.slice(startIndex, endIndex);

      paginatedProducts.forEach((product, index) => {
        const card = createProductCard(product, index);
        grid.appendChild(card);
      });

      // Update pagination
      updatePagination(products.length);

      // Show filter slider
      document.getElementById('filterSliderContainer').style.display = 'block';
    }

    // Create product card
function createProductCard(product, index) {
  const card = document.createElement('div');
  card.className = 'product-card';
  card.style.animationDelay = `${index * 0.1}s`;
  
  const discountPercent = calculateDiscountPercent(product.realPrice, product.discountedPrice);
  const showBadge = discountPercent >= 10;
  const isFree = parseFloat(product.discountedPrice) === 0;

  card.innerHTML = `
    ${showBadge && !isFree ? `<div class="product-badge">${discountPercent}% OFF</div>` : ''}
    ${isFree ? `<div class="product-badge" style="background: linear-gradient(135deg, #00ff88, #00ffff);">FREE</div>` : ''}
    <img src="${escapeHtml(product.imageUrl)}" alt="${escapeHtml(product.title)}" class="product-image" 
         onerror="this.src='https://via.placeholder.com/300x180/1a0a2e/00ffff?text=No+Image'" loading="lazy">
    <div class="product-title">${escapeHtml(product.title)}</div>
    <div class="product-description">${escapeHtml(product.description || '')}</div>
    <div class="product-price-section">
      ${!isFree ? `<span class="product-price-original">${formatCurrency(product.realPrice)}</span>` : ''}
      <span class="product-price-discount">${isFree ? 'FREE' : formatCurrency(product.discountedPrice)}</span>
    </div>
    <div class="product-actions">
      <button class="btn" onclick="showProductDetail('${product.id}')">
        <i class="fas fa-eye"></i> View
      </button>
      ${!isFree ? `
        <button class="btn-icon" onclick="quickAddToCart('${product.id}'); event.stopPropagation();" title="Quick Add to Cart">
          <i class="fas fa-cart-plus"></i>
        </button>
      ` : ''}
    </div>
  `;

  card.onclick = (e) => {
    if (!e.target.closest('button')) {
      showProductDetail(product.id);
    }
  };

  return card;
}

    // Show product detail
    async function showProductDetail(productId) {
      try {
        showLoading('Loading product...');
        const snapshot = await window.dbGet(window.dbRef(window.db, `products/${productId}`));
        hideLoading();
        
        if (snapshot.exists()) {
          window.currentProduct = { id: productId, ...snapshot.val() };
          const product = window.currentProduct;

          document.getElementById('modalImage').src = product.imageUrl;
          document.getElementById('modalTitle').textContent = product.title;
          document.getElementById('modalDescription').textContent = product.description;
          
          const isFree = parseFloat(product.discountedPrice) === 0;
          
          if (!isFree) {
            document.getElementById('modalPriceOriginal').textContent = formatCurrency(product.realPrice);
            document.getElementById('modalPriceOriginal').style.display = 'inline';
          } else {
            document.getElementById('modalPriceOriginal').style.display = 'none';
          }
          
          document.getElementById('modalPriceDiscount').textContent = isFree ? 'FREE' : formatCurrency(product.discountedPrice);

          const discountPercent = calculateDiscountPercent(product.realPrice, product.discountedPrice);
          const badge = document.getElementById('modalDiscountBadge');
          if (discountPercent >= 10 && !isFree) {
            badge.textContent = `Save ${discountPercent}%`;
            badge.style.display = 'inline-block';
          } else {
            badge.style.display = 'none';
          }

          // Display screenshots if available
          const screenshotsSection = document.getElementById('screenshotsSection');
          const screenshotsGrid = document.getElementById('screenshotsGrid');
          
          if (product.screenshots && product.screenshots.length > 0) {
            screenshotsGrid.innerHTML = '';
            product.screenshots.forEach((screenshot, idx) => {
              const img = document.createElement('img');
              img.src = screenshot;
              img.alt = `Screenshot ${idx + 1}`;
              img.className = 'screenshot-item';
              img.onclick = () => showScreenshotPreview(screenshot);
              img.onerror = function() {
                this.style.display = 'none';
              };
              screenshotsGrid.appendChild(img);
            });
            screenshotsSection.style.display = 'block';
          } else {
            screenshotsSection.style.display = 'none';
          }

          // Update buttons based on price
          const buttonGroup = document.getElementById('modalButtonGroup');

          if (isFree) {
            buttonGroup.innerHTML = `
              <button class="btn btn-free-download btn-full" onclick="window.open('${escapeHtml(product.downloadLink || '#')}', '_blank')">
                <i class="fas fa-download"></i> Free Download
              </button>
              <button class="btn-icon" id="bookmarkBtn" onclick="toggleBookmark()" title="Bookmark">
                <i class="far fa-bookmark"></i>
              </button>
            `;
          } else {
            buttonGroup.innerHTML = `
              <button class="btn" onclick="addToCart()">
                <i class="fas fa-shopping-cart"></i> Add to Cart
              </button>
              <button class="btn btn-secondary" onclick="buyNow()">
                <i class="fas fa-bolt"></i> Buy Now
              </button>
              <button class="btn-icon" id="bookmarkBtn" onclick="toggleBookmark()" title="Bookmark">
                <i class="far fa-bookmark"></i>
              </button>
            `;
          }

          // Update bookmark button
          await updateBookmarkButton();

          document.getElementById('productModal').classList.add('active');
          document.body.style.overflow = 'hidden';
        }
      } catch (error) {
        hideLoading();
        console.error('Error loading product:', error);
        showNotification('Failed to load product', 'error');
      }
    }

    // Show screenshot preview
    function showScreenshotPreview(imageUrl) {
      document.getElementById('screenshotPreview').src = imageUrl;
      document.getElementById('screenshotModal').classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    // Update bookmark button
    async function updateBookmarkButton() {
      const btn = document.getElementById('bookmarkBtn');
      if (!window.currentUser || !window.currentProduct) {
        btn.querySelector('i').className = 'far fa-bookmark';
        return;
      }

      try {
        const snapshot = await window.dbGet(
          window.dbRef(window.db, `users/${window.currentUser.uid}/bookmarks/${window.currentProduct.id}`)
        );
        
        if (snapshot.exists()) {
          btn.querySelector('i').className = 'fas fa-bookmark';
          btn.classList.add('active');
        } else {
          btn.querySelector('i').className = 'far fa-bookmark';
          btn.classList.remove('active');
        }
      } catch (error) {
        console.error('Error checking bookmark:', error);
      }
    }

    // Toggle bookmark
    async function toggleBookmark() {
      if (!window.currentUser) {
        closeModal('productModal');
        showNotification('Please login to bookmark products', 'error');
        showAuth();
        return;
      }

      if (!window.currentProduct) return;

      try {
        const bookmarkRef = window.dbRef(
          window.db,
          `users/${window.currentUser.uid}/bookmarks/${window.currentProduct.id}`
        );
        
        const snapshot = await window.dbGet(bookmarkRef);
        const btn = document.getElementById('bookmarkBtn');
        
        if (snapshot.exists()) {
          await window.dbRemove(bookmarkRef);
          btn.querySelector('i').className = 'far fa-bookmark';
          btn.classList.remove('active');
          showNotification('Removed from bookmarks', 'success');
        } else {
          await window.dbSet(bookmarkRef, {
            productId: window.currentProduct.id,
            addedAt: new Date().toISOString()
          });
          btn.querySelector('i').className = 'fas fa-bookmark';
          btn.classList.add('active');
          showNotification('Added to bookmarks', 'success');
        }
      } catch (error) {
        console.error('Error toggling bookmark:', error);
        showNotification('Failed to update bookmark', 'error');
      }
    }

    // Search products
    function searchProducts() {
      const query = document.getElementById('searchBar').value.toLowerCase().trim();
      
      let filtered = window.allProducts;

      if (query) {
        filtered = window.allProducts.filter(product => 
          product.title.toLowerCase().includes(query) ||
          (product.description && product.description.toLowerCase().includes(query))
        );
      }

      // Apply current filter
      if (window.currentFilter !== 'all') {
        filtered = applyFilter(filtered, window.currentFilter);
      }

      currentPage = 1;
      displayProducts(filtered);

      if (query && filtered.length === 0) {
        displayEmptyState('search');
      }
    }

    // Filter products
    function filterProducts(filter) {
      window.currentFilter = filter;
      
      // Update active button
      document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
          btn.classList.add('active');
        }
      });

      let filtered = window.allProducts;

      if (filter !== 'all') {
        filtered = applyFilter(window.allProducts, filter);
      }

      currentPage = 1;
      displayProducts(filtered);
    }

    // Apply filter logic
function applyFilter(products, filter) {
  switch(filter) {
    case 'premium':
      // Premium Products: all paid products that are NOT Budget Friendly (discount below 70%)
      return products.filter(p => {
        const realPrice = parseFloat(p.realPrice);
        const discountedPrice = parseFloat(p.discountedPrice);
        if (!(discountedPrice > 0)) return false;
        const discountPercent = realPrice > 0 ? ((realPrice - discountedPrice) / realPrice) * 100 : 0;
        return discountPercent < 70;
      });
    
    case 'budget':
      // Budget Friendly: 70% discount or more (excludes free products)
      return products.filter(p => {
        const realPrice = parseFloat(p.realPrice);
        const discountedPrice = parseFloat(p.discountedPrice);
        if (!(realPrice > 0) || discountedPrice === 0) return false;
        const discountPercent = ((realPrice - discountedPrice) / realPrice) * 100;
        return discountPercent >= 70;
      });
    
    case 'free':
      // Free Products: Price is 0
      return products.filter(p => {
        const price = parseFloat(p.discountedPrice);
        return price === 0;
      });
    
    default:
      // All Products
      return products;
  }
}

    // Update pagination
    function updatePagination(totalItems) {
      const pagination = document.getElementById('pagination');
      const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

      if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
      }

      pagination.style.display = 'flex';
      pagination.innerHTML = '';

      // Previous button
      const prevBtn = document.createElement('button');
      prevBtn.className = 'pagination-btn';
      prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i> Previous';
      prevBtn.disabled = currentPage === 1;
      prevBtn.onclick = () => {
        if (currentPage > 1) {
          currentPage--;
          displayProducts(getFilteredProducts());
          scrollToTop();
        }
      };
      pagination.appendChild(prevBtn);

      // Page numbers
      for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
          const pageBtn = document.createElement('button');
          pageBtn.className = `pagination-btn ${i === currentPage ? 'active' : ''}`;
          pageBtn.textContent = i;
          pageBtn.onclick = () => {
            currentPage = i;
            displayProducts(getFilteredProducts());
            scrollToTop();
          };
          pagination.appendChild(pageBtn);
        } else if (i === currentPage - 2 || i === currentPage + 2) {
          const dots = document.createElement('span');
          dots.textContent = '...';
          dots.style.padding = '10px';
          dots.style.color = '#999';
          pagination.appendChild(dots);
        }
      }

      // Next button
      const nextBtn = document.createElement('button');
      nextBtn.className = 'pagination-btn';
      nextBtn.innerHTML = 'Next <i class="fas fa-chevron-right"></i>';
      nextBtn.disabled = currentPage === totalPages;
      nextBtn.onclick = () => {
        if (currentPage < totalPages) {
          currentPage++;
          displayProducts(getFilteredProducts());
          scrollToTop();
        }
      };
      pagination.appendChild(nextBtn);
    }

    // Get filtered products
    function getFilteredProducts() {
      const query = document.getElementById('searchBar').value.toLowerCase().trim();
      let filtered = window.allProducts;

      if (query) {
        filtered = filtered.filter(product => 
          product.title.toLowerCase().includes(query) ||
          (product.description && product.description.toLowerCase().includes(query))
        );
      }

      if (window.currentFilter !== 'all') {
        filtered = applyFilter(filtered, window.currentFilter);
      }

      return filtered;
    }

    // Cart functions
    function loadCartFromStorage() {
      try {
        const savedCart = localStorage.getItem('shoppingCart');
        if (savedCart) {
          window.cart = JSON.parse(savedCart);
          updateCartUI();
        }
      } catch (error) {
        console.error('Error loading cart:', error);
        window.cart = [];
      }
    }

    function saveCartToStorage() {
      try {
        localStorage.setItem('shoppingCart', JSON.stringify(window.cart));
      } catch (error) {
        console.error('Error saving cart:', error);
      }
    }

    function updateCartUI() {
      const badge = document.getElementById('cartBadge');
      const cartItems = document.getElementById('cartItems');
      const cartTotal = document.getElementById('cartTotal');
      const cartTotalAmount = document.getElementById('cartTotalAmount');
      const checkoutBtn = document.getElementById('cartCheckoutBtn');

      if (window.cart.length === 0) {
        badge.style.display = 'none';
        cartItems.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🛒</div>
            <div class="empty-title">Cart is Empty</div>
            <div class="empty-text">Add products to your cart to get started!</div>
          </div>
        `;
        cartTotal.style.display = 'none';
        checkoutBtn.disabled = true;
        return;
      }

      badge.textContent = window.cart.length;
      badge.style.display = 'block';
      cartTotal.style.display = 'block';
      checkoutBtn.disabled = false;

      let total = 0;
      cartItems.innerHTML = '';

      window.cart.forEach((item, index) => {
        total += parseFloat(item.price);
        
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';
        cartItem.innerHTML = `
          <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" class="cart-item-image"
               onerror="this.src='https://via.placeholder.com/80/1a0a2e/00ffff?text=No+Image'">
          <div class="cart-item-details">
            <div class="cart-item-title">${escapeHtml(item.title)}</div>
            <div class="cart-item-price">${formatCurrency(item.price)}</div>
          </div>
          <div class="cart-item-remove" onclick="removeFromCart(${index})" title="Remove">
            <i class="fas fa-times"></i>
          </div>
        `;
        cartItems.appendChild(cartItem);
      });

      cartTotalAmount.textContent = formatCurrency(total);
    }

    function toggleCart() {
      const cartSidebar = document.getElementById('cartSidebar');
      const overlay = document.getElementById('sidebarOverlay');
      
      cartSidebar.classList.toggle('active');
      overlay.classList.toggle('active');
      
      if (cartSidebar.classList.contains('active')) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    }

    async function addToCart() {
      if (!window.currentProduct) return;

      const product = window.currentProduct;
      const cartItem = {
        id: product.id,
        title: product.title,
        price: product.discountedPrice,
        image: product.imageUrl
      };

      window.cart.push(cartItem);
      saveCartToStorage();
      updateCartUI();
      
      showNotification(`${product.title} added to cart!`, 'success');
      
      // Close modal and open cart
      closeModal('productModal');
      setTimeout(() => {
        toggleCart();
      }, 300);
    }

    async function quickAddToCart(productId) {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, `products/${productId}`));
        
        if (snapshot.exists()) {
          const product = snapshot.val();
          const cartItem = {
            id: productId,
            title: product.title,
            price: product.discountedPrice,
            image: product.imageUrl
          };

          window.cart.push(cartItem);
          saveCartToStorage();
          updateCartUI();
          
          showNotification(`${product.title} added to cart!`, 'success');
        }
      } catch (error) {
        console.error('Error adding to cart:', error);
        showNotification('Failed to add to cart', 'error');
      }
    }

    function removeFromCart(index) {
      const removedItem = window.cart[index];
      
      showConfirmDialog(
        'Remove from Cart',
        `Are you sure you want to remove "${removedItem.title}" from cart?`,
        (confirmed) => {
          if (confirmed) {
            window.cart.splice(index, 1);
            saveCartToStorage();
            updateCartUI();
            showNotification(`${removedItem.title} removed from cart`, 'success');
          }
        }
      );
    }

    function clearCart() {
      window.cart = [];
      saveCartToStorage();
      updateCartUI();
    }

    // Buy Now function
    function buyNow() {
      if (!window.currentProduct) return;

      // Clear cart and add only this product
      window.cart = [{
        id: window.currentProduct.id,
        title: window.currentProduct.title,
        price: window.currentProduct.discountedPrice,
        image: window.currentProduct.imageUrl
      }];
      
      saveCartToStorage();
      updateCartUI();
      
      closeModal('productModal');
      
      setTimeout(() => {
        checkoutCart();
      }, 300);
    }

    // Checkout functions
    function checkoutCart() {
      if (!window.currentUser) {
        showNotification('Please login to checkout', 'error');
        showAuth();
        return;
      }

      if (window.cart.length === 0) {
        showNotification('Your cart is empty', 'error');
        return;
      }

      // Close cart sidebar if open
      document.getElementById('cartSidebar').classList.remove('active');
      document.getElementById('sidebarOverlay').classList.remove('active');

      // Display checkout items
      const checkoutItems = document.getElementById('checkoutItems');
      checkoutItems.innerHTML = '<h3 style="color: #00ffff; margin-bottom: 15px;"><i class="fas fa-shopping-bag"></i> Order Summary</h3>';

      window.cart.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'cart-item';
        itemDiv.innerHTML = `
          <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" class="cart-item-image"
               onerror="this.src='https://via.placeholder.com/80/1a0a2e/00ffff?text=No+Image'">
          <div class="cart-item-details">
            <div class="cart-item-title">${escapeHtml(item.title)}</div>
            <div class="cart-item-price">${formatCurrency(item.price)}</div>
          </div>
        `;
        checkoutItems.appendChild(itemDiv);
      });

      // Calculate totals
      const subtotal = window.cart.reduce((sum, item) => sum + parseFloat(item.price), 0);
      document.getElementById('checkoutSubtotal').textContent = formatCurrency(subtotal);
      document.getElementById('checkoutTotal').textContent = formatCurrency(subtotal);
      document.getElementById('discountRow').style.display = 'none';

      // Reset coupon
      window.appliedCoupon = null;
      document.getElementById('couponInput').value = '';
      document.getElementById('couponMessage').style.display = 'none';
      document.getElementById('appliedCouponDisplay').style.display = 'none';
      document.getElementById('couponInputSection').style.display = 'block';

      document.getElementById('checkoutModal').classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    // Coupon functions
    async function applyCoupon() {
      const couponCode = document.getElementById('couponInput').value.trim().toUpperCase();
      
      if (!couponCode) {
        showCouponMessage('Please enter a coupon code', 'error');
        return;
      }

      try {
        showLoading('Validating coupon...');
        
        const couponsSnapshot = await window.dbGet(window.dbRef(window.db, 'coupons'));
        hideLoading();
        
        if (!couponsSnapshot.exists()) {
          showCouponMessage('Invalid coupon code', 'error');
          return;
        }

        const coupons = couponsSnapshot.val();
        let foundCoupon = null;
        let couponId = null;

        for (const [id, coupon] of Object.entries(coupons)) {
          if (coupon.code === couponCode) {
            foundCoupon = coupon;
            couponId = id;
            break;
          }
        }

        if (!foundCoupon) {
          showCouponMessage('Invalid coupon code', 'error');
          return;
        }

        // Validate coupon
        const now = Date.now();

        if (!foundCoupon.isActive) {
          showCouponMessage('This coupon is no longer active', 'error');
          return;
        }

        if (foundCoupon.expiryDate && new Date(foundCoupon.expiryDate).getTime() <= now) {
          showCouponMessage('This coupon has expired', 'error');
          return;
        }

        if (foundCoupon.usageLimit > 0 && (foundCoupon.usedCount || 0) >= foundCoupon.usageLimit) {
          showCouponMessage('This coupon has reached its usage limit', 'error');
          return;
        }

        const subtotal = window.cart.reduce((sum, item) => sum + parseFloat(item.price), 0);

        if (foundCoupon.minAmount > 0 && subtotal < foundCoupon.minAmount) {
          showCouponMessage(`Minimum purchase amount is ${formatCurrency(foundCoupon.minAmount)}`, 'error');
          return;
        }

        // Calculate discount
        let discountAmount = 0;

        if (foundCoupon.discountType === 'percentage') {
          discountAmount = (subtotal * foundCoupon.discountValue) / 100;
          
          if (foundCoupon.maxDiscount > 0 && discountAmount > foundCoupon.maxDiscount) {
            discountAmount = foundCoupon.maxDiscount;
          }
        } else {
          discountAmount = foundCoupon.discountValue;
        }

        // Apply coupon
        window.appliedCoupon = {
          id: couponId,
          code: foundCoupon.code,
          discount: discountAmount
        };

        updateCheckoutTotals();
        
        // Show applied coupon
        document.getElementById('couponInputSection').style.display = 'none';
        document.getElementById('appliedCouponDisplay').innerHTML = `
          <div class="applied-coupon">
            <div>
              <i class="fas fa-ticket-alt"></i> 
              <span class="applied-coupon-code">${foundCoupon.code}</span>
              <span style="color: #00ff88; margin-left: 10px;">+${formatCurrency(discountAmount)}</span>
            </div>
            <div class="applied-coupon-remove" onclick="removeCoupon()">
              <i class="fas fa-times"></i>
            </div>
          </div>
        `;
        document.getElementById('appliedCouponDisplay').style.display = 'block';

        showNotification('Coupon applied successfully!', 'success');

      } catch (error) {
        hideLoading();
        console.error('Error applying coupon:', error);
        showCouponMessage('Failed to apply coupon', 'error');
      }
    }

    function removeCoupon() {
      window.appliedCoupon = null;
      document.getElementById('couponInput').value = '';
      document.getElementById('appliedCouponDisplay').style.display = 'none';
      document.getElementById('couponInputSection').style.display = 'block';
      updateCheckoutTotals();
      showNotification('Coupon removed', 'success');
    }

    function showCouponMessage(message, type) {
      const messageDiv = document.getElementById('couponMessage');
      messageDiv.textContent = message;
      messageDiv.className = `coupon-message ${type}`;
      messageDiv.style.display = 'block';
      
      setTimeout(() => {
        messageDiv.style.display = 'none';
      }, 3000);
    }

    function updateCheckoutTotals() {
      const subtotal = window.cart.reduce((sum, item) => sum + parseFloat(item.price), 0);
      document.getElementById('checkoutSubtotal').textContent = formatCurrency(subtotal);

      if (window.appliedCoupon) {
        document.getElementById('discountRow').style.display = 'flex';
        document.getElementById('checkoutDiscount').textContent = `+${formatCurrency(window.appliedCoupon.discount)}`;
        
        const total = subtotal + window.appliedCoupon.discount;
        document.getElementById('checkoutTotal').textContent = formatCurrency(total);
      } else {
        document.getElementById('discountRow').style.display = 'none';
        document.getElementById('checkoutTotal').textContent = formatCurrency(subtotal);
      }
    }

    // Proceed to payment
    function proceedToPayment() {
      if (window.cart.length === 0) {
        showNotification('Cart is empty', 'error');
        return;
      }

      // Calculate total
      const subtotal = window.cart.reduce((sum, item) => sum + parseFloat(item.price), 0);
      const discount = window.appliedCoupon ? window.appliedCoupon.discount : 0;
      const total = subtotal + discount;

      document.getElementById('paymentAmount').textContent = formatCurrency(total);

      closeModal('checkoutModal');
      
      setTimeout(() => {
        document.getElementById('paymentModal').classList.add('active');
        document.body.style.overflow = 'hidden';
      }, 300);
    }

    // Confirm purchase
    async function confirmPurchase() {
      const userAmount = document.getElementById('userAmount').value.trim();
      const utrId = document.getElementById('utrId').value.trim();

      // Validation
      if (!userAmount) {
        showNotification('Please enter the amount you paid', 'error');
        return;
      }

      if (!utrId) {
        showNotification('Please enter UTR ID', 'error');
        return;
      }

      const amountPaid = parseFloat(userAmount);
      if (isNaN(amountPaid) || amountPaid <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
      }

      if (utrId.length < 10 || utrId.length > 16) {
        showNotification('UTR ID must be between 10 and 16 characters', 'error');
        return;
      }

      if (!/^[a-zA-Z0-9]+$/.test(utrId)) {
        showNotification('UTR ID must contain only letters and numbers', 'error');
        return;
      }

      try {
        showLoading('Processing your order...');

        // Calculate totals
        const subtotal = window.cart.reduce((sum, item) => sum + parseFloat(item.price), 0);
        const discount = window.appliedCoupon ? window.appliedCoupon.discount : 0;
        const total = subtotal + discount;

        // Create orders for each product in cart
        for (const item of window.cart) {
          const orderRef = window.dbPush(window.dbRef(window.db, 'orders'));
          const orderId = orderRef.key;

          const orderData = {
            productId: item.id,
            amountPaid: amountPaid,
            productSnapshot: {
              title: item.title,
              imageUrl: item.image,
              discountedPrice: item.price
            },
            userInput: { 
              utrId,
              name: window.currentUser.displayName || 'N/A',
              email: window.currentUser.email,
              phone: 'N/A'
            },
            userId: window.currentUser.uid,
            userEmail: window.currentUser.email,
            couponUsed: window.appliedCoupon ? window.appliedCoupon.code : null,
            discountAmount: window.appliedCoupon ? window.appliedCoupon.discount : 0,
            finalAmount: total,
            status: 'pending',
            createdAt: new Date().toISOString()
          };

          await window.dbSet(orderRef, orderData);
          
          // Add to user's purchases
          await window.dbSet(
            window.dbRef(window.db, `users/${window.currentUser.uid}/purchases/${orderId}`),
            {
              orderId: orderId,
              productId: item.id,
              purchasedAt: new Date().toISOString()
            }
          );
        }

        // Update coupon usage if applied
        if (window.appliedCoupon) {
          const couponRef = window.dbRef(window.db, `coupons/${window.appliedCoupon.id}`);
          const couponSnapshot = await window.dbGet(couponRef);
          
          if (couponSnapshot.exists()) {
            const currentUsage = couponSnapshot.val().usedCount || 0;
            await window.dbUpdate(couponRef, {
              usedCount: currentUsage + 1
            });
          }
        }

        hideLoading();

        // Clear cart
        clearCart();
        window.appliedCoupon = null;

        // Clear form
        document.getElementById('userAmount').value = '';
        document.getElementById('utrId').value = '';

        closeModal('paymentModal');
        
        showNotification('🎉 Order placed successfully! Check your purchase history.', 'success');

        // Show success animation
        setTimeout(() => {
          showPurchaseHistory();
        }, 1500);

      } catch (error) {
        hideLoading();
        console.error('Error placing order:', error);
        showNotification('Failed to place order: ' + error.message, 'error');
      }
    }

    // Show products page
    function showProducts() {
      toggleMenu();
      
      document.getElementById('mainContent').innerHTML = `
  <div class="filter-slider-container" id="filterSliderContainer">
    <div class="filter-slider" id="filterSlider">
      <button class="filter-btn active" data-filter="all" onclick="filterProducts('all')">
        <i class="fas fa-th"></i> All Products
      </button>
      <button class="filter-btn" data-filter="premium" onclick="filterProducts('premium')">
        <i class="fas fa-star"></i> Premium Product
      </button>
      <button class="filter-btn" data-filter="budget" onclick="filterProducts('budget')">
        <i class="fas fa-fire"></i> Budget Friendly
      </button>
      <button class="filter-btn" data-filter="free" onclick="filterProducts('free')">
        <i class="fas fa-tag"></i> Free Product
      </button>
    </div>
  </div>
  <h2 class="section-title"><i class="fas fa-shopping-bag"></i> Products</h2>
  <div id="productsGrid" class="products-grid"></div>
  <div class="pagination" id="pagination" style="display: none;"></div>
`;

      window.currentFilter = 'all';
      currentPage = 1;
      loadProducts();
      
      document.getElementById('searchBar').value = '';
    }

    // Show bookmarks
    async function showBookmarks() {
      if (!window.currentUser) {
        requireLogin('view bookmarks');
        return;
      }

      toggleMenu();
      
      try {
        showLoading('Loading bookmarks...');
        
        const snapshot = await window.dbGet(
          window.dbRef(window.db, `users/${window.currentUser.uid}/bookmarks`)
        );
        
        hideLoading();

        document.getElementById('mainContent').innerHTML = `
          <h2 class="section-title"><i class="fas fa-bookmark"></i> My Bookmarks</h2>
          <div id="bookmarksGrid" class="products-grid"></div>
        `;

        const grid = document.getElementById('bookmarksGrid');

        if (snapshot.exists()) {
          const bookmarks = snapshot.val();
          const bookmarkIds = Object.keys(bookmarks);
          
          // Load each bookmarked product
          const bookmarkedProducts = [];
          for (const productId of bookmarkIds) {
            const productSnapshot = await window.dbGet(
              window.dbRef(window.db, `products/${productId}`)
            );
            if (productSnapshot.exists()) {
              bookmarkedProducts.push({
                id: productId,
                ...productSnapshot.val()
              });
            }
          }
          
          if (bookmarkedProducts.length > 0) {
            bookmarkedProducts.forEach((product, index) => {
              const card = createProductCard(product, index);
              grid.appendChild(card);
            });
          } else {
            displayEmptyState('bookmarks');
          }
        } else {
          displayEmptyState('bookmarks');
        }
      } catch (error) {
        hideLoading();
        console.error('Error loading bookmarks:', error);
        showNotification('Failed to load bookmarks', 'error');
        displayEmptyState('bookmarks');
      }
    }

    // Show purchase history
    async function showPurchaseHistory() {
      if (!window.currentUser) {
        requireLogin('view purchase history');
        return;
      }

      toggleMenu();

      try {
        showLoading('Loading purchase history...');

        const snapshot = await window.dbGet(
          window.dbRef(window.db, `users/${window.currentUser.uid}/purchases`)
        );

        hideLoading();

        document.getElementById('mainContent').innerHTML = `
          <h2 class="section-title"><i class="fas fa-history"></i> Purchase History</h2>
          <div id="purchasesList"></div>
        `;

        const list = document.getElementById('purchasesList');

        if (snapshot.exists()) {
          const purchases = Object.values(snapshot.val())
            .sort((a, b) => new Date(b.purchasedAt) - new Date(a.purchasedAt));
          
          // Load order details for each purchase
          for (const purchase of purchases) {
            const orderSnapshot = await window.dbGet(
              window.dbRef(window.db, `orders/${purchase.orderId}`)
            );
            
            if (orderSnapshot.exists()) {
              const order = orderSnapshot.val();
              
              // Load product details to get download link
              const productSnapshot = await window.dbGet(
                window.dbRef(window.db, `products/${purchase.productId}`)
              );
              
              let downloadLink = null;
              if (productSnapshot.exists()) {
                downloadLink = productSnapshot.val().downloadLink || null;
              }
              
              const card = createOrderCard(purchase.orderId, order, downloadLink);
              list.appendChild(card);
            }
          }
        } else {
          displayEmptyState('orders');
        }
      } catch (error) {
        hideLoading();
        console.error('Error loading purchases:', error);
        showNotification('Failed to load purchase history', 'error');
        displayEmptyState('orders');
      }
    }

    // Create order card with download button
    function createOrderCard(orderId, order, downloadLink) {
      const card = document.createElement('div');
      card.className = 'order-card';
      
      const date = new Date(order.createdAt).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      const status = order.status || 'pending';
      const statusClass = status === 'confirmed' ? 'confirmed' : (status === 'processing' ? 'processing' : 'pending');
      const statusText = status.charAt(0).toUpperCase() + status.slice(1);

      // Show download button only if status is confirmed and download link exists
      const showDownloadBtn = status === 'confirmed' && downloadLink;

      card.innerHTML = `
        <div class="order-header">
          <div>
            <div class="order-id"><i class="fas fa-receipt"></i> Order #${orderId.substring(0, 8)}</div>
            <div class="order-date"><i class="far fa-clock"></i> ${date}</div>
          </div>
          <div class="order-status ${statusClass}">${statusText}</div>
        </div>
        <div class="order-body">
          <img src="${escapeHtml(order.productSnapshot?.imageUrl || '')}" 
               alt="${escapeHtml(order.productSnapshot?.title || 'Product')}" 
               class="order-image"
               onerror="this.src='https://via.placeholder.com/80/1a0a2e/00ffff?text=No+Image'">
          <div class="order-details">
            <div class="order-product-title">${escapeHtml(order.productSnapshot?.title || 'Product')}</div>
            <div class="order-price">${formatCurrency(order.finalAmount || order.productSnapshot?.discountedPrice || 0)}</div>
            ${order.couponUsed ? `<div style="font-size: 12px; color: #00ff88; margin-top: 5px;">
              <i class="fas fa-ticket-alt"></i> Coupon: ${escapeHtml(order.couponUsed)} 
              (+${formatCurrency(order.discountAmount || 0)})
            </div>` : ''}
          </div>
        </div>
        <div class="order-footer">
          <div class="order-utr">
            <strong>UTR ID:</strong> ${escapeHtml(order.userInput?.utrId || 'N/A')}
          </div>
          <div style="font-size: 12px; color: #999;">
            <i class="fas fa-user"></i> ${escapeHtml(order.userInput?.name || 'N/A')}
          </div>
          ${showDownloadBtn ? `
            <button class="download-btn" onclick="window.open('${escapeHtml(downloadLink)}', '_blank')">
              <i class="fas fa-download"></i> Download
            </button>
          ` : ''}
        </div>
      `;

      return card;
    }

    // Show admin support chat
    function showAdminSupport() {
      if (!window.currentUser) {
        requireLogin('contact admin support');
        return;
      }

      toggleMenu();
      
      document.getElementById('chatModal').classList.add('active');
      document.body.style.overflow = 'hidden';
      
      loadChatMessages();
    }

    // Load chat messages
    async function loadChatMessages() {
      if (!window.currentUser) return;

      try {
        const chatRef = window.dbRef(window.db, `chats/${window.currentUser.uid}/messages`);
        
        window.dbOnValue(chatRef, (snapshot) => {
          const messagesContainer = document.getElementById('chatMessages');
          messagesContainer.innerHTML = '';

          if (snapshot.exists()) {
            const messages = Object.entries(snapshot.val()).map(([id, msg]) => ({
              id,
              ...msg
            })).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

            messages.forEach(msg => {
              const messageDiv = createChatMessage(msg);
              messagesContainer.appendChild(messageDiv);
            });

            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          } else {
            messagesContainer.innerHTML = `
              <div class="chat-empty-state">
                <div class="chat-empty-icon">💬</div>
                <div>Start a conversation with admin</div>
              </div>
            `;
          }
        });
      } catch (error) {
        console.error('Error loading chat messages:', error);
      }
    }

    // Create chat message element
    function createChatMessage(msg) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `chat-message ${msg.sender === 'user' ? 'user' : 'admin'}`;
      
      const time = new Date(msg.timestamp).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
      });

      messageDiv.innerHTML = `
        <div class="chat-message-avatar">
          ${msg.sender === 'user' ? 'U' : 'A'}
        </div>
        <div>
          <div class="chat-message-content">
            ${escapeHtml(msg.message)}
          </div>
          <div class="chat-message-time">${time}</div>
        </div>
      `;

      return messageDiv;
    }

    // Send chat message
    async function sendMessage() {
      if (!window.currentUser) return;

      const input = document.getElementById('chatInput');
      const message = input.value.trim();

      if (!message) {
        showNotification('Please enter a message', 'error');
        return;
      }

      try {
        const chatRef = window.dbRef(window.db, `chats/${window.currentUser.uid}/messages`);
        const newMessageRef = window.dbPush(chatRef);

        await window.dbSet(newMessageRef, {
          message: message,
          sender: 'user',
          timestamp: new Date().toISOString(),
          userName: window.currentUser.displayName || window.currentUser.email
        });

        // Update chat info
        await window.dbSet(window.dbRef(window.db, `chats/${window.currentUser.uid}/info`), {
          lastMessage: message,
          lastMessageTime: new Date().toISOString(),
          userName: window.currentUser.displayName || window.currentUser.email,
          userEmail: window.currentUser.email
        });

        input.value = '';
        showNotification('Message sent', 'success');

      } catch (error) {
        console.error('Error sending message:', error);
        showNotification('Failed to send message', 'error');
      }
    }

    // Handle Enter key in chat input
    document.addEventListener('DOMContentLoaded', function() {
      const chatInput = document.getElementById('chatInput');
      if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
          }
        });
      }
    });

    // Show contact page
    async function showContact() {
      toggleMenu();

      try {
        showLoading('Loading contact information...');
        
        const snapshot = await window.dbGet(window.dbRef(window.db, 'meta/contact'));
        
        hideLoading();

        let contactInfo = {};
        if (snapshot.exists()) {
          contactInfo = snapshot.val();
        }

        document.getElementById('mainContent').innerHTML = `
          <h2 class="section-title"><i class="fas fa-phone"></i> Contact Us</h2>
          <div class="contact-card page-transition">
            <div class="contact-item">
              <div class="contact-label"><i class="fas fa-store"></i> Brand Name</div>
              <div class="contact-value">${escapeHtml(contactInfo.brandName || 'N/A')}</div>
            </div>
            <div class="contact-item">
              <div class="contact-label"><i class="fas fa-user-tie"></i> Legal Operator</div>
              <div class="contact-value">${escapeHtml(contactInfo.operator || 'N/A')}</div>
            </div>
            <div class="contact-item">
              <div class="contact-label"><i class="fas fa-envelope"></i> Email</div>
              <div class="contact-value">${escapeHtml(contactInfo.email || 'N/A')}</div>
            </div>
            <div class="contact-item">
              <div class="contact-label"><i class="fas fa-phone"></i> Phone</div>
              <div class="contact-value">${escapeHtml(contactInfo.phone || 'N/A')}</div>
            </div>
            ${contactInfo.socialYoutube || contactInfo.socialTelegram ? `
              <div class="social-links">
                ${contactInfo.socialYoutube ? `
                  <a href="${escapeHtml(contactInfo.socialYoutube)}" target="_blank" class="social-btn">
                    <i class="fab fa-instagram"></i> Instagram
                  </a>
                ` : ''}
                ${contactInfo.socialTelegram ? `
                  <a href="${escapeHtml(contactInfo.socialTelegram)}" target="_blank" class="social-btn">
                    <i class="fab fa-telegram"></i> Telegram
                  </a>
                ` : ''}
              </div>
            ` : ''}
          </div>

          <h2 class="section-title" style="margin-top: 40px;"><i class="fas fa-file-contract"></i> Terms & Policies</h2>
          <div class="accordion page-transition">
            <div class="accordion-item">
              <div class="accordion-header" onclick="toggleAccordion(this)">
                <span><i class="fas fa-undo"></i> Refund Policy</span>
                <span class="accordion-icon">▼</span>
              </div>
              <div class="accordion-content">
                <p class="accordion-text">
                   Thank you for purchasing our digital product.
Please read this Refund & Cancellation Policy carefully before making a payment on our platform.

1. Instant Access

All our products are delivered instantly after successful payment.
Once payment is completed, the download link for your purchased digital item (HTML, ZIP, code file, etc.) becomes immediately available to you.

                </p>
              </div>
            </div>

            <div class="accordion-item">
              <div class="accordion-header" onclick="toggleAccordion(this)">
                <span><i class="fas fa-file-contract"></i> Terms & Conditions</span>
                <span class="accordion-icon">▼</span>
              </div>
              <div class="accordion-content">
                <p class="accordion-text">
                  By using our service, you agree to our terms and conditions. All products are subject to availability. We reserve the right to modify prices and product offerings without prior notice. Users must provide accurate information during checkout. You are responsible for maintaining the confidentiality of your account. Unauthorized use of our service may result in account termination.
                </p>
              </div>
            </div>

            <div class="accordion-item">
              <div class="accordion-header" onclick="toggleAccordion(this)">
                <span><i class="fas fa-shield-alt"></i> Privacy Policy</span>
                <span class="accordion-icon">▼</span>
              </div>
              <div class="accordion-content">
                <p class="accordion-text">
                  We collect and store user information securely using industry-standard encryption. Your data is used only for order processing, communication, and improving our services. We do not share your personal information with third parties without consent, except as required by law. Your payment information is processed securely through trusted payment gateways. You have the right to request access to, modification of, or deletion of your personal data at any time.
                </p>
              </div>
            </div>

            <div class="accordion-item">
              <div class="accordion-header" onclick="toggleAccordion(this)">
                <span><i class="fas fa-credit-card"></i> Payment Policy</span>
                <span class="accordion-icon">▼</span>
              </div>
              <div class="accordion-content">
                <p class="accordion-text">
                  We accept payments through UPI, Bank Transfer, and other secure payment methods. All prices are in USDT ($) unless otherwise stated. Payment must be completed before product delivery or access. We use secure SSL encryption for all transactions. After payment, please provide the UTR/Transaction ID for verification. Orders are processed only after payment confirmation.
                </p>
              </div>
            </div>

            <div class="accordion-item">
              <div class="accordion-header" onclick="toggleAccordion(this)">
                <span><i class="fas fa-ticket-alt"></i> Coupon Policy</span>
                <span class="accordion-icon">▼</span>
              </div>
              <div class="accordion-content">
                <p class="accordion-text">
                  Coupons are subject to terms and conditions specified at the time of issue. Only one coupon can be applied per order. Coupons cannot be combined with other offers unless explicitly stated. Expired coupons cannot be used or extended. Coupon discounts are applied to the product price before taxes and shipping. We reserve the right to cancel or modify coupons at any time without prior notice.
                </p>
              </div>
            </div>
          </div>
        `;
      } catch (error) {
        hideLoading();
        console.error('Error loading contact:', error);
        showNotification('Failed to load contact information', 'error');
      }
    }

    // Toggle accordion
    function toggleAccordion(header) {
      const item = header.parentElement;
      const wasActive = item.classList.contains('active');
      
      // Close all accordions
      document.querySelectorAll('.accordion-item').forEach(i => i.classList.remove('active'));
      
      // Open clicked accordion if it wasn't active
      if (!wasActive) {
        item.classList.add('active');
      }
    }

    // Auth functions
    function showAuth() {
      if (window.currentUser) {
        toggleMenu();
        return;
      }

      document.getElementById('authModal').classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    function switchToSignup() {
      document.getElementById('authTitle').innerHTML = '<i class="fas fa-user-plus"></i> Sign Up';
      document.getElementById('loginForm').style.display = 'none';
      document.getElementById('signupForm').style.display = 'block';
    }

    function switchToLogin() {
      document.getElementById('authTitle').innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
      document.getElementById('signupForm').style.display = 'none';
      document.getElementById('loginForm').style.display = 'block';
    }

    async function loginUser() {
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value.trim();

      if (!email || !password) {
        showNotification('Please fill all fields', 'error');
        return;
      }

      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
      }

      try {
        showLoading('Logging in...');
        await window.authSignIn(window.auth, email, password);
        hideLoading();
        
        closeModal('authModal');
        
        document.getElementById('loginEmail').value = '';
        document.getElementById('loginPassword').value = '';
        
        showNotification(`Welcome back, ${window.currentUser.displayName || 'User'}!`, 'success');
      } catch (error) {
        hideLoading();
        console.error('Login error:', error);
        
        let errorMsg = 'Login failed';
        if (error.code === 'auth/user-not-found') {
          errorMsg = 'No account found with this email';
        } else if (error.code === 'auth/wrong-password') {
          errorMsg = 'Incorrect password';
        } else if (error.code === 'auth/invalid-email') {
          errorMsg = 'Invalid email format';
        } else if (error.code === 'auth/too-many-requests') {
          errorMsg = 'Too many failed attempts. Please try again later';
        } else {
          errorMsg = error.message;
        }
        
        showNotification(errorMsg, 'error');
      }
    }

    async function signupUser() {
      const name = document.getElementById('signupName').value.trim();
      const email = document.getElementById('signupEmail').value.trim();
      const password = document.getElementById('signupPassword').value.trim();

      if (!name || !email || !password) {
        showNotification('Please fill all fields', 'error');
        return;
      }

      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
      }

      if (password.length < 6) {
        showNotification('Password must be at least 6 characters', 'error');
        return;
      }

      try {
        showLoading('Creating account...');
        const userCredential = await window.authCreateUser(window.auth, email, password);
        await window.authUpdateProfile(userCredential.user, { displayName: name });
        
        // Create user profile in database
        await window.dbSet(window.dbRef(window.db, `users/${userCredential.user.uid}/profile`), {
          name: name,
          email: email,
          createdAt: new Date().toISOString()
        });
        
        hideLoading();
        
        closeModal('authModal');
        
        document.getElementById('signupName').value = '';
        document.getElementById('signupEmail').value = '';
        document.getElementById('signupPassword').value = '';
        
        showNotification(`Welcome to our store, ${name}!`, 'success');
      } catch (error) {
        hideLoading();
        console.error('Signup error:', error);
        
        let errorMsg = 'Signup failed';
        if (error.code === 'auth/email-already-in-use') {
          errorMsg = 'This email is already registered';
        } else if (error.code === 'auth/invalid-email') {
          errorMsg = 'Invalid email format';
        } else if (error.code === 'auth/weak-password') {
          errorMsg = 'Password is too weak';
        } else {
          errorMsg = error.message;
        }
        
        showNotification(errorMsg, 'error');
      }
    }

    async function logoutUser() {
      try {
        showLoading('Logging out...');
        await window.authSignOut(window.auth);
        hideLoading();
        
        toggleMenu();
        showProducts();
        
        showNotification('Logged out successfully', 'success');
      } catch (error) {
        hideLoading();
        console.error('Logout error:', error);
        showNotification('Logout failed', 'error');
      }
    }

    // ===== Games (Spin & Win / Scratch & Win) =====
    // Both games share one daily play limit and draw prizes from the same
    // live coupon pool the admin manages in admin.html.
    window.gameState = {
      segments: [],
      isSpinning: false,
      eligible: false,
      scratchReward: null,
      scratchRevealed: false,
      scratchDrawing: false
    };

    const GAME_ONE_DAY_MS = 24 * 60 * 60 * 1000;

    function openGamesModal() {
      if (!window.currentUser) {
        requireLogin('play games and earn coupons');
        return;
      }
      toggleMenu();
      document.getElementById('gamesGridView').style.display = 'block';
      document.getElementById('spinWheelView').style.display = 'none';
      document.getElementById('scratchCardView').style.display = 'none';
      document.getElementById('gamesModal').classList.add('active');
      document.body.style.overflow = 'hidden';
      refreshGamesGridEligibility();
    }

    function backToGamesGrid() {
      document.getElementById('gamesGridView').style.display = 'block';
      document.getElementById('spinWheelView').style.display = 'none';
      document.getElementById('scratchCardView').style.display = 'none';
      refreshGamesGridEligibility();
    }

    // Checks whether the user has already played (either game) today,
    // and greys out both game cards on the picker screen if so.
    async function refreshGamesGridEligibility() {
      const banner = document.getElementById('gamesAlreadyPlayedBanner');
      const bannerText = document.getElementById('gamesAlreadyPlayedText');
      const spinCard = document.getElementById('spinGameCard');
      const scratchCard = document.getElementById('scratchGameCard');

      try {
        const { alreadyPlayed, hoursLeft } = await getGamePlayStatus();
        if (alreadyPlayed) {
          banner.style.display = 'block';
          bannerText.textContent = `You've already played today. Come back in ${hoursLeft} hour${hoursLeft === 1 ? '' : 's'}!`;
          spinCard.classList.add('coming-soon');
          scratchCard.classList.add('coming-soon');
        } else {
          banner.style.display = 'none';
          spinCard.classList.remove('coming-soon');
          scratchCard.classList.remove('coming-soon');
        }
      } catch (error) {
        // If we can't check, fail open on the picker screen — the game
        // view itself will re-check and block the actual play if needed.
        banner.style.display = 'none';
      }
    }

    async function getGamePlayStatus() {
      const uid = window.currentUser.uid;
      const snapshot = await window.dbGet(window.dbRef(window.db, `gamePlays/${uid}/lastPlayed`));
      const lastPlayed = snapshot.exists() ? snapshot.val() : 0;
      const msSince = Date.now() - lastPlayed;

      if (lastPlayed && msSince < GAME_ONE_DAY_MS) {
        const hoursLeft = Math.ceil((GAME_ONE_DAY_MS - msSince) / (60 * 60 * 1000));
        return { alreadyPlayed: true, hoursLeft };
      }
      return { alreadyPlayed: false, hoursLeft: 0 };
    }

    // Fetches active, non-expired, under-usage-limit coupons — the exact
    // same rules applied at real checkout — so only genuinely valid
    // coupons can ever be won.
    async function getValidGameCoupons() {
      const couponsSnapshot = await window.dbGet(window.dbRef(window.db, 'coupons'));
      const now = Date.now();
      let validCoupons = [];

      if (couponsSnapshot.exists()) {
        const coupons = couponsSnapshot.val();
        validCoupons = Object.entries(coupons)
          .filter(([id, c]) => {
            if (!c.isActive) return false;
            if (c.expiryDate && new Date(c.expiryDate).getTime() <= now) return false;
            if (c.usageLimit > 0 && (c.usedCount || 0) >= c.usageLimit) return false;
            return true;
          })
          .map(([id, c]) => ({ id, code: c.code }));
      }
      return validCoupons;
    }

    // Records that the user has played today (locks out BOTH games until
    // tomorrow) and, on a win, records which coupon they were shown.
    async function recordGamePlay(wonCode) {
      const uid = window.currentUser.uid;
      await window.dbSet(window.dbRef(window.db, `gamePlays/${uid}/lastPlayed`), Date.now());
      if (wonCode) {
        await window.dbSet(window.dbRef(window.db, `gamePlays/${uid}/lastCoupon`), wonCode);
      }
    }

    function copySpinCoupon(code) {
      navigator.clipboard.writeText(code).then(() => {
        showNotification('Coupon code copied!');
      }).catch(() => {
        showNotification('Could not copy — please copy it manually', 'error');
      });
    }

    // ---------- Spin & Win ----------
    async function openSpinWheel() {
      document.getElementById('gamesGridView').style.display = 'none';
      document.getElementById('spinWheelView').style.display = 'block';

      const spinBtn = document.getElementById('spinBtn');
      const statusEl = document.getElementById('spinStatus');
      const resultEl = document.getElementById('spinResult');
      resultEl.className = 'spin-result';
      resultEl.innerHTML = '';
      spinBtn.disabled = true;
      statusEl.textContent = 'Loading...';

      try {
        const { alreadyPlayed, hoursLeft } = await getGamePlayStatus();
        if (alreadyPlayed) {
          window.gameState.eligible = false;
          statusEl.textContent = `You've already played today. Come back in ${hoursLeft} hour${hoursLeft === 1 ? '' : 's'}!`;
          renderWheelSegments([]);
          return;
        }

        const validCoupons = await getValidGameCoupons();

        if (validCoupons.length === 0) {
          window.gameState.eligible = false;
          statusEl.textContent = 'No coupons available to win right now — check back soon!';
          renderWheelSegments([]);
          return;
        }

        // Keep the wheel readable: use up to 6 real coupon slots
        const shuffled = validCoupons.sort(() => Math.random() - 0.5).slice(0, 6);

        window.gameState.eligible = true;
        renderWheelSegments(shuffled);
        statusEl.textContent = 'Good luck!';
        spinBtn.disabled = false;
      } catch (error) {
        statusEl.textContent = 'Error loading the game: ' + error.message;
      }
    }

    function renderWheelSegments(realCoupons) {
      const TOTAL_SEGMENTS = 8;
      const segments = realCoupons.map(c => ({ type: 'coupon', label: c.code, code: c.code }));
      while (segments.length < TOTAL_SEGMENTS) {
        segments.push({ type: 'lose', label: 'Try Again' });
      }
      segments.sort(() => Math.random() - 0.5);

      window.gameState.segments = segments;

      const winColors = ['#00ffff', '#a855f7', '#00ff88', '#ffa500'];
      const loseColor = '#241432';

      const anglePer = 360 / TOTAL_SEGMENTS;
      let gradientParts = [];
      let labelHtml = '';

      segments.forEach((seg, i) => {
        const color = seg.type === 'coupon' ? winColors[i % winColors.length] : loseColor;
        const start = i * anglePer;
        const end = start + anglePer;
        gradientParts.push(`${color} ${start}deg ${end}deg`);

        const midAngle = start + anglePer / 2;
        labelHtml += `<div class="wheel-segment-label" style="transform: rotate(${midAngle}deg) translateY(-95px);">${escapeHtml(seg.label)}</div>`;
      });

      const wheel = document.getElementById('spinWheel');
      wheel.style.background = `conic-gradient(${gradientParts.join(', ')})`;
      wheel.style.transition = 'none';
      wheel.style.transform = 'rotate(0deg)';
      void wheel.offsetWidth; // force reflow before re-enabling the transition
      wheel.style.transition = 'transform 4.5s cubic-bezier(0.12, 0.85, 0.2, 1)';

      wheel.innerHTML = `<div class="wheel-center">🎁</div>${labelHtml}`;
    }

    function spinWheel() {
      if (window.gameState.isSpinning || !window.gameState.eligible) return;

      const segments = window.gameState.segments;
      if (!segments || segments.length === 0) return;

      window.gameState.isSpinning = true;
      document.getElementById('spinBtn').disabled = true;
      document.getElementById('spinStatus').textContent = 'Spinning...';
      document.getElementById('spinResult').className = 'spin-result';
      document.getElementById('spinResult').innerHTML = '';

      const TOTAL_SEGMENTS = segments.length;
      const anglePer = 360 / TOTAL_SEGMENTS;
      const winningIndex = Math.floor(Math.random() * TOTAL_SEGMENTS);
      const midAngle = winningIndex * anglePer + anglePer / 2;
      const jitter = (Math.random() - 0.5) * (anglePer * 0.5);

      const extraSpins = 5 * 360;
      const targetRotation = extraSpins + ((360 - midAngle + jitter + 360) % 360);

      const wheel = document.getElementById('spinWheel');
      wheel.style.transform = `rotate(${targetRotation}deg)`;

      const onDone = () => {
        wheel.removeEventListener('transitionend', onDone);
        handleSpinResult(segments[winningIndex]);
      };
      wheel.addEventListener('transitionend', onDone);
    }

    async function handleSpinResult(segment) {
      window.gameState.isSpinning = false;
      window.gameState.eligible = false;

      const statusEl = document.getElementById('spinStatus');
      const resultEl = document.getElementById('spinResult');

      try {
        await recordGamePlay(segment.type === 'coupon' ? segment.code : null);

        if (segment.type === 'coupon') {
          statusEl.textContent = '';
          resultEl.className = 'spin-result win';
          resultEl.innerHTML = `
            <div style="font-size: 32px;">🎉</div>
            <div>You won a coupon!</div>
            <div class="spin-coupon-code">${escapeHtml(segment.code)}</div>
            <button class="btn btn-primary" style="margin-top: 5px;" onclick="copySpinCoupon('${segment.code.replace(/'/g, "\\'")}')">
              <i class="fas fa-copy"></i> Copy Code
            </button>
            <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 8px;">
              Use this code at checkout. Come back tomorrow to play again!
            </div>
          `;
          showNotification('🎉 You won a coupon!');
        } else {
          statusEl.textContent = '';
          resultEl.className = 'spin-result lose';
          resultEl.innerHTML = `
            <div style="font-size: 28px;">😅</div>
            <div>Better luck next time!</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 8px;">
              Come back tomorrow to play again!
            </div>
          `;
        }
      } catch (error) {
        statusEl.textContent = 'Error saving your result: ' + error.message;
      }
    }

    // ---------- Scratch & Win ----------
    async function openScratchCard() {
      document.getElementById('gamesGridView').style.display = 'none';
      document.getElementById('scratchCardView').style.display = 'block';

      window.gameState.scratchReward = null;
      window.gameState.scratchRevealed = false;

      const statusEl = document.getElementById('scratchStatus');
      const resultEl = document.getElementById('scratchResult');
      const revealEl = document.getElementById('scratchReveal');
      resultEl.className = 'spin-result';
      resultEl.innerHTML = '';
      revealEl.innerHTML = '';
      statusEl.textContent = 'Loading...';

      try {
        const { alreadyPlayed, hoursLeft } = await getGamePlayStatus();
        if (alreadyPlayed) {
          statusEl.textContent = `You've already played today. Come back in ${hoursLeft} hour${hoursLeft === 1 ? '' : 's'}!`;
          drawScratchOverlay(false);
          return;
        }

        const validCoupons = await getValidGameCoupons();

        if (validCoupons.length === 0) {
          statusEl.textContent = 'No coupons available to win right now — check back soon!';
          drawScratchOverlay(false);
          return;
        }

        // Same odds shape as the wheel: up to 6 "slots" worth of chance,
        // the rest are a loss, so both games are equally fair.
        const winChance = Math.min(validCoupons.length, 6) / 8;
        const isWin = Math.random() < winChance;

        if (isWin) {
          const winner = validCoupons[Math.floor(Math.random() * validCoupons.length)];
          window.gameState.scratchReward = { type: 'coupon', code: winner.code };
          revealEl.innerHTML = `
            <div style="font-size: 28px;">🎉</div>
            <div style="font-size: 13px; margin-top: 4px;">You won!</div>
            <div class="spin-coupon-code" style="font-size: 18px;">${escapeHtml(winner.code)}</div>
          `;
        } else {
          window.gameState.scratchReward = { type: 'lose' };
          revealEl.innerHTML = `
            <div style="font-size: 26px;">😅</div>
            <div style="font-size: 13px; margin-top: 4px;">Better luck next time!</div>
          `;
        }

        statusEl.textContent = 'Scratch the card to reveal your prize!';
        drawScratchOverlay(true);
      } catch (error) {
        statusEl.textContent = 'Error loading the game: ' + error.message;
        drawScratchOverlay(false);
      }
    }

    function drawScratchOverlay(scratchable) {
      const canvas = document.getElementById('scratchCanvas');
      const ctx = canvas.getContext('2d');

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.globalCompositeOperation = 'source-over';

      const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
      gradient.addColorStop(0, '#8a8fa3');
      gradient.addColorStop(1, '#5b5f73');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      ctx.font = 'bold 15px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(scratchable ? '✨ Scratch Here ✨' : 'Not available right now', canvas.width / 2, canvas.height / 2);

      canvas.style.pointerEvents = scratchable ? 'auto' : 'none';
      if (scratchable) {
        setupScratchListeners(canvas, ctx);
      }
    }

    function setupScratchListeners(canvas, ctx) {
      // Avoid stacking duplicate listeners across game sessions
      const freshCanvas = canvas.cloneNode(true);
      canvas.parentNode.replaceChild(freshCanvas, canvas);
      const freshCtx = freshCanvas.getContext('2d');
      freshCtx.drawImage(canvas, 0, 0);

      const scratch = (clientX, clientY) => {
        const rect = freshCanvas.getBoundingClientRect();
        const x = (clientX - rect.left) * (freshCanvas.width / rect.width);
        const y = (clientY - rect.top) * (freshCanvas.height / rect.height);

        freshCtx.globalCompositeOperation = 'destination-out';
        freshCtx.beginPath();
        freshCtx.arc(x, y, 18, 0, Math.PI * 2);
        freshCtx.fill();
      };

      const checkScratchProgress = () => {
        const imageData = freshCtx.getImageData(0, 0, freshCanvas.width, freshCanvas.height).data;
        let cleared = 0;
        const sampleStep = 4; // sample every 4th pixel's alpha channel for performance
        let sampled = 0;
        for (let i = 3; i < imageData.length; i += 4 * sampleStep) {
          sampled++;
          if (imageData[i] < 40) cleared++;
        }
        const percentCleared = cleared / sampled;
        if (percentCleared > 0.5 && !window.gameState.scratchRevealed) {
          window.gameState.scratchRevealed = true;
          freshCanvas.style.transition = 'opacity 0.4s';
          freshCanvas.style.opacity = '0';
          setTimeout(() => { freshCanvas.style.pointerEvents = 'none'; }, 400);
          finishScratchCard();
        }
      };

      let drawing = false;

      freshCanvas.addEventListener('mousedown', (e) => { drawing = true; scratch(e.clientX, e.clientY); });
      freshCanvas.addEventListener('mousemove', (e) => { if (drawing) { scratch(e.clientX, e.clientY); checkScratchProgress(); } });
      window.addEventListener('mouseup', () => { drawing = false; });

      freshCanvas.addEventListener('touchstart', (e) => {
        drawing = true;
        const t = e.touches[0];
        scratch(t.clientX, t.clientY);
        e.preventDefault();
      }, { passive: false });
      freshCanvas.addEventListener('touchmove', (e) => {
        if (drawing) {
          const t = e.touches[0];
          scratch(t.clientX, t.clientY);
          checkScratchProgress();
        }
        e.preventDefault();
      }, { passive: false });
      freshCanvas.addEventListener('touchend', () => { drawing = false; });
    }

    async function finishScratchCard() {
      const statusEl = document.getElementById('scratchStatus');
      const resultEl = document.getElementById('scratchResult');
      const reward = window.gameState.scratchReward;

      try {
        await recordGamePlay(reward && reward.type === 'coupon' ? reward.code : null);

        if (reward && reward.type === 'coupon') {
          statusEl.textContent = '';
          resultEl.className = 'spin-result win';
          resultEl.innerHTML = `
            <div style="font-size: 32px;">🎉</div>
            <div>You won a coupon!</div>
            <div class="spin-coupon-code">${escapeHtml(reward.code)}</div>
            <button class="btn btn-primary" style="margin-top: 5px;" onclick="copySpinCoupon('${reward.code.replace(/'/g, "\\'")}')">
              <i class="fas fa-copy"></i> Copy Code
            </button>
            <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 8px;">
              Use this code at checkout. Come back tomorrow to play again!
            </div>
          `;
          showNotification('🎉 You won a coupon!');
        } else {
          statusEl.textContent = '';
          resultEl.className = 'spin-result lose';
          resultEl.innerHTML = `
            <div style="font-size: 28px;">😅</div>
            <div>Better luck next time!</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 8px;">
              Come back tomorrow to play again!
            </div>
          `;
        }
      } catch (error) {
        statusEl.textContent = 'Error saving your result: ' + error.message;
      }
    }

    // Require login
    function requireLogin(feature) {
      toggleMenu();
      showNotification(`Please login to ${feature}`, 'error');
      setTimeout(() => {
        showAuth();
      }, 500);
    }

    // Close modal
    function closeModal(modalId) {
      document.getElementById(modalId).classList.remove('active');
      document.body.style.overflow = '';
    }

    // Close modal on outside click
    window.onclick = function(event) {
      if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
        document.body.style.overflow = '';
      }
    }

    // Display empty state
    function displayEmptyState(type) {
      const grid = type === 'products' ? document.getElementById('productsGrid') : 
                   type === 'bookmarks' ? document.getElementById('bookmarksGrid') :
                   type === 'orders' ? document.getElementById('purchasesList') :
                   document.getElementById('productsGrid');

      const emptyStates = {
        products: {
          icon: '📦',
          title: 'No Products Available',
          text: 'Check back later for new products!'
        },
        search: {
          icon: '🔍',
          title: 'No Results Found',
          text: 'Try different search terms'
        },
        bookmarks: {
          icon: '🔖',
          title: 'No Bookmarks Yet',
          text: 'Bookmark your favorite products to find them easily later'
        },
        orders: {
          icon: '🛒',
          title: 'No Orders Yet',
          text: 'Start shopping and your orders will appear here'
        }
      };

      const state = emptyStates[type] || emptyStates.products;

      grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">${state.icon}</div>
          <div class="empty-title">${state.title}</div>
          <div class="empty-text">${state.text}</div>
        </div>
      `;
    }

    // Scroll to top
    function scrollToTop() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }

    // Show/hide FAB on scroll
    window.addEventListener('scroll', function() {
      const fab = document.getElementById('fab');
      if (window.scrollY > 500) {
        fab.classList.add('show');
      } else {
        fab.classList.remove('show');
      }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
      // Escape key closes modals and dialogs
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
          modal.classList.remove('active');
          document.body.style.overflow = '';
        });
        
        if (document.getElementById('confirmDialog').classList.contains('active')) {
          hideConfirmDialog();
        }
        
        // Close cart sidebar
        if (document.getElementById('cartSidebar').classList.contains('active')) {
          toggleCart();
        }
        
        // Close menu sidebar
        if (document.getElementById('sidebar').classList.contains('active')) {
          toggleMenu();
        }
      }

      // Ctrl/Cmd + K focuses search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchBar').focus();
      }
    });

    // Handle authentication state changes in realtime
    window.auth.onAuthStateChanged((user) => {
      if (user && !window.currentUser) {
        // User just logged in
        updateMenu();
      } else if (!user && window.currentUser) {
        // User just logged out
        updateMenu();
      }
    });

    // Prevent form submission on Enter key in modals
    document.querySelectorAll('.modal input').forEach(input => {
      input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          
          const modal = this.closest('.modal');
          const submitBtn = modal.querySelector('.btn');
          if (submitBtn) {
            submitBtn.click();
          }
        }
      });
    });

    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';

    // Initialize page
    window.addEventListener('load', function() {
      // Hide loading overlay if still showing
      hideLoading();
      
      // Load initial products
      loadProducts();
      
      // Update menu
      updateMenu();
      
      // Load cart from storage
      loadCartFromStorage();

      console.log('%c🚀 Premium Shop Loaded Successfully! 🚀', 'color: #00ffff; font-size: 20px; font-weight: bold;');
      console.log('%c✨ New Features: Free Download, Games Coupon Link, Fixed QR, Amount Input ✨', 'color: #a855f7; font-size: 14px;');
    });

    // Handle online/offline status
    window.addEventListener('online', () => {
      showNotification('🟢 Connection restored', 'success');
    });

    window.addEventListener('offline', () => {
      showNotification('🔴 You are offline. Some features may not work.', 'error');
    });

    // Auto-save cart on page unload
    window.addEventListener('beforeunload', function() {
      saveCartToStorage();
    });

    // Handle visibility change (tab switching)
    document.addEventListener('visibilitychange', function() {
      if (!document.hidden) {
        // Refresh data when user comes back to the tab
        if (window.currentUser) {
          loadProducts();
        }
      }
    });

    // Console art
    console.log(`
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║   🛒 PREMIUM SHOP - USER PANEL 🛒    ║
    ║                                       ║
    ║   Version: 3.1.0                      ║
    ║   Features:                           ║
    ║   ✓ Real-time Product Sync            ║
    ║   ✓ Shopping Cart System              ║
    ║   ✓ Coupon Management                 ║
    ║   ✓ Bookmark Products                 ║
    ║   ✓ Purchase History                  ║
    ║   ✓ Download Links (Confirmed Orders) ║
    ║   ✓ Product Screenshots Gallery       ║
    ║   ✓ Admin Support Chat                ║
    ║   ✓ FREE Product Downloads            ║
    ║   ✓ Games Coupon Link                 ║
    ║   ✓ Fixed QR Code Payment             ║
    ║   ✓ Amount Input Field                ║
    ║   ✓ 2-Column Grid Layout              ║
    ║   ✓ Swipe Filter Slider               ║
    ║   ✓ FIT_CENTER Product Images         ║
    ║   ✓ Confirm Delete Dialog             ║
    ║   ✓ Smooth Animations                 ║
    ║   ✓ Mobile Responsive                 ║
    ║                                       ║
    ║   Connected to Firebase ✅            ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    `);

    // Debug mode (only in development)
    const DEBUG_MODE = false;

    if (DEBUG_MODE) {
      window.debugCart = () => console.log('Cart:', window.cart);
      window.debugUser = () => console.log('User:', window.currentUser);
      window.debugProducts = () => console.log('Products:', window.allProducts);
      console.log('%c🐛 Debug mode enabled. Use debugCart(), debugUser(), debugProducts()', 'color: #ffa500;');
    }
  </script>
</body>
</html>""".encode("utf-8")

ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Premium Admin Panel v3.0</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 50%, #0a0a0a 100%);
      color: #e0e0e0;
      min-height: 100vh;
      overflow-x: hidden;
    }

    .drawer-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(5px);
      z-index: 998;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
    }

    .drawer-overlay.active {
      opacity: 1;
      visibility: visible;
    }

    .drawer {
      position: fixed;
      top: 0;
      left: 0;
      width: min(320px, 85vw);
      height: 100%;
      background: linear-gradient(180deg, rgba(26, 10, 46, 0.98) 0%, rgba(10, 10, 10, 0.98) 100%);
      backdrop-filter: blur(20px);
      border-right: 1px solid rgba(0, 255, 255, 0.2);
      z-index: 999;
      transition: transform 0.3s ease;
      transform: translateX(-100%);
      overflow-y: auto;
      box-shadow: 4px 0 30px rgba(0, 255, 255, 0.3);
    }

    .drawer.active {
      transform: translateX(0);
    }

    .drawer-header {
      padding: 30px 20px;
      border-bottom: 1px solid rgba(0, 255, 255, 0.2);
      background: rgba(0, 255, 255, 0.05);
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .drawer-close-btn {
      position: absolute;
      top: 15px;
      right: 15px;
      width: 35px;
      height: 35px;
      background: rgba(255, 0, 110, 0.2);
      border: 1px solid #ff006e;
      border-radius: 50%;
      color: #ff006e;
      font-size: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
    }

    .drawer-close-btn:hover {
      background: #ff006e;
      color: #fff;
      transform: rotate(90deg);
    }

    .drawer-brand {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 15px;
    }

    .drawer-logo {
      width: 50px;
      height: 50px;
      border-radius: 12px;
      object-fit: cover;
      border: 2px solid #00ffff;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
    }

    .drawer-brand-name {
      font-size: 20px;
      font-weight: bold;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .drawer-user-info {
      font-size: 14px;
      color: #999;
      padding: 10px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 8px;
      border: 1px solid rgba(0, 255, 255, 0.1);
    }

    .drawer-user-info strong {
      color: #00ffff;
      display: block;
      margin-bottom: 5px;
    }

    .drawer-nav {
      padding: 20px 0;
    }

    .drawer-nav-item {
      display: flex;
      align-items: center;
      gap: 15px;
      padding: 15px 20px;
      color: #e0e0e0;
      text-decoration: none;
      transition: all 0.3s ease;
      border-left: 3px solid transparent;
      cursor: pointer;
      user-select: none;
    }

    .drawer-nav-item:hover {
      background: rgba(0, 255, 255, 0.1);
      border-left-color: #00ffff;
      padding-left: 30px;
    }

    .drawer-nav-item.active {
      background: rgba(0, 255, 255, 0.15);
      border-left-color: #00ffff;
      color: #00ffff;
    }

    .drawer-nav-icon {
      font-size: 20px;
      width: 24px;
      text-align: center;
    }

    .drawer-footer {
      padding: 20px;
      border-top: 1px solid rgba(0, 255, 255, 0.2);
      margin-top: auto;
    }

    .menu-toggle {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 45px;
      height: 45px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(0, 255, 255, 0.3);
      position: fixed;
      top: 20px;
      left: 20px;
      z-index: 100;
    }

    .menu-toggle:hover {
      transform: translateY(-2px) rotate(90deg);
      box-shadow: 0 6px 20px rgba(0, 255, 255, 0.5);
    }

    .menu-toggle span {
      display: block;
      width: 20px;
      height: 2px;
      background: #000;
      position: relative;
      transition: all 0.3s ease;
    }

    .menu-toggle span::before,
    .menu-toggle span::after {
      content: '';
      position: absolute;
      width: 20px;
      height: 2px;
      background: #000;
      transition: all 0.3s ease;
    }

    .menu-toggle span::before {
      top: -6px;
    }

    .menu-toggle span::after {
      bottom: -6px;
    }

    .menu-toggle.active span {
      background: transparent;
    }

    .menu-toggle.active span::before {
      top: 0;
      transform: rotate(45deg);
    }

    .menu-toggle.active span::after {
      bottom: 0;
      transform: rotate(-45deg);
    }

    .menu-toggle.hidden {
      display: none;
    }

    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }

    .login-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 24px;
      padding: 40px;
      width: 100%;
      max-width: 400px;
      box-shadow: 0 8px 32px rgba(0, 255, 255, 0.2);
      animation: fadeIn 0.5s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-20px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .login-title {
      font-size: 32px;
      text-align: center;
      margin-bottom: 30px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
    }

    .input-group {
      margin-bottom: 20px;
    }

    .input-group label {
      display: block;
      margin-bottom: 8px;
      color: #00ffff;
      font-size: 14px;
    }

    .input-group input, .input-group textarea, .input-group select {
      width: 100%;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 12px;
      color: #fff;
      font-size: 16px;
      transition: all 0.3s ease;
    }

    .input-group input:focus, .input-group textarea:focus, .input-group select:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
      background: rgba(255, 255, 255, 0.08);
    }

    .input-group textarea {
      resize: vertical;
      min-height: 100px;
    }

    .input-group select {
      cursor: pointer;
    }

    .input-group select option {
      background: #1a0a2e;
      color: #fff;
    }

    .btn {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 12px;
      color: #000;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.5);
    }

    .btn:active {
      transform: translateY(0);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    .btn::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 0;
      height: 0;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.3);
      transform: translate(-50%, -50%);
      transition: width 0.6s, height 0.6s;
    }

    .btn:active::before {
      width: 300px;
      height: 300px;
    }

    .admin-container {
      display: none;
      padding: 80px 20px 20px 20px;
      transition: padding-left 0.3s ease;
    }

    .header {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 30px;
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 15px;
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .brand-logo {
      width: 50px;
      height: 50px;
      border-radius: 12px;
      object-fit: cover;
      border: 2px solid #00ffff;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
    }

    .brand-name {
      font-size: 24px;
      font-weight: bold;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .tabs {
      display: none;
    }

    .tab-content {
      display: none;
      animation: fadeIn 0.5s ease;
    }

    .tab-content.active {
      display: block;
    }

    .card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 30px;
      margin-bottom: 20px;
      box-shadow: 0 8px 32px rgba(0, 255, 255, 0.15);
      transition: all 0.3s ease;
    }

    .card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 255, 255, 0.25);
    }

    .card-title {
      font-size: 24px;
      margin-bottom: 20px;
      color: #00ffff;
      text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
    }

    .products-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
    }

    .product-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      transition: all 0.3s ease;
    }

    .product-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(168, 85, 247, 0.3);
      border-color: rgba(168, 85, 247, 0.5);
    }

    .product-image {
      width: 100%;
      height: 200px;
      object-fit: cover;
      border-radius: 12px;
      margin-bottom: 15px;
      border: 2px solid rgba(0, 255, 255, 0.3);
    }

    .product-title {
      font-size: 18px;
      font-weight: bold;
      margin-bottom: 10px;
      color: #00ffff;
    }

    .product-price {
      margin-bottom: 15px;
    }

    .price-original {
      text-decoration: line-through;
      color: #999;
      margin-right: 10px;
    }

    .price-discount {
      color: #00ff88;
      font-size: 20px;
      font-weight: bold;
      text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }

    .btn-group {
      display: flex;
      gap: 10px;
    }

    .btn-small {
      flex: 1;
      padding: 10px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: bold;
      transition: all 0.3s ease;
    }

    .btn-edit {
      background: linear-gradient(135deg, #00ffff, #0099ff);
      color: #000;
    }

    .btn-delete {
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      color: #fff;
    }

    .btn-small:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.4);
    }

    .orders-list {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .order-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      transition: all 0.3s ease;
    }

    .order-card:hover {
      transform: translateX(4px);
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.3);
    }

    .order-info {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 10px;
      margin-top: 10px;
    }

    .order-field {
      color: #00ffff;
      font-size: 14px;
    }

    .order-value {
      color: #fff;
      font-weight: bold;
    }

    .error-message {
      background: rgba(255, 0, 0, 0.1);
      border: 1px solid rgba(255, 0, 0, 0.3);
      border-radius: 12px;
      padding: 15px;
      margin-bottom: 20px;
      color: #ff6b6b;
      text-align: center;
    }

    .success-message {
      background: rgba(0, 255, 0, 0.1);
      border: 1px solid rgba(0, 255, 0, 0.3);
      border-radius: 12px;
      padding: 15px;
      margin-bottom: 20px;
      color: #51cf66;
      text-align: center;
    }

    .loading-spinner {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 3px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: #00ffff;
      animation: spin 1s linear infinite;
      margin-right: 10px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      text-align: center;
      transition: all 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.3);
    }

    .stat-value {
      font-size: 36px;
      font-weight: bold;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 10px;
    }

    .stat-label {
      color: #999;
      font-size: 14px;
    }

    .search-box {
      margin-bottom: 20px;
    }

    .search-box input {
      width: 100%;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 12px;
      color: #fff;
      font-size: 16px;
    }

    .filter-buttons {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .filter-btn {
      padding: 8px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 8px;
      color: #00ffff;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 14px;
    }

    .filter-btn.active {
      background: linear-gradient(135deg, #00ffff, #a855f7);
      color: #000;
    }

    .filter-btn:hover {
      transform: translateY(-2px);
    }

    .coupons-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
    }

    .coupon-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .coupon-card::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent, rgba(0, 255, 255, 0.1), transparent);
      transform: rotate(45deg);
      transition: all 0.5s ease;
    }

    .coupon-card:hover::before {
      top: -100%;
      right: -100%;
    }

    .coupon-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 255, 255, 0.3);
      border-color: rgba(0, 255, 255, 0.5);
    }

    .coupon-code {
      font-size: 24px;
      font-weight: bold;
      color: #00ffff;
      margin-bottom: 10px;
      text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
      letter-spacing: 2px;
    }

    .coupon-discount {
      font-size: 32px;
      font-weight: bold;
      background: linear-gradient(135deg, #00ff88, #00ffff);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 10px;
    }

    .coupon-description {
      color: #ccc;
      font-size: 14px;
      margin-bottom: 15px;
      line-height: 1.6;
    }

    .coupon-details {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 15px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 10px;
      margin-bottom: 15px;
    }

    .coupon-detail-item {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
    }

    .coupon-detail-label {
      color: #999;
    }

    .coupon-detail-value {
      color: #00ffff;
      font-weight: bold;
    }

    .coupon-status {
      display: inline-block;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      margin-bottom: 15px;
    }

    .coupon-status.active {
      background: rgba(0, 255, 136, 0.2);
      color: #00ff88;
      border: 1px solid #00ff88;
    }

    .coupon-status.inactive {
      background: rgba(255, 107, 107, 0.2);
      color: #ff6b6b;
      border: 1px solid #ff6b6b;
    }

    .coupon-status.expired {
      background: rgba(255, 165, 0, 0.2);
      color: #ffa500;
      border: 1px solid #ffa500;
    }

    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: #999;
    }

    .empty-state-icon {
      font-size: 64px;
      margin-bottom: 20px;
      opacity: 0.5;
    }

    .empty-state-title {
      font-size: 20px;
      color: #00ffff;
      margin-bottom: 10px;
    }

    .empty-state-text {
      font-size: 14px;
      line-height: 1.6;
    }

    .fab {
      position: fixed;
      bottom: 30px;
      right: 30px;
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border-radius: 50%;
      border: none;
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.5);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      color: #000;
      transition: all 0.3s ease;
      z-index: 100;
    }

    .fab:hover {
      transform: scale(1.1) rotate(90deg);
      box-shadow: 0 12px 32px rgba(0, 255, 255, 0.7);
    }

    .fab:active {
      transform: scale(0.95) rotate(90deg);
    }

    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(5px);
      z-index: 9999;
      display: none;
      align-items: center;
      justify-content: center;
    }

    .loading-overlay.active {
      display: flex;
    }

    .loading-content {
      text-align: center;
    }

    .loading-spinner-large {
      width: 60px;
      height: 60px;
      border: 5px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: #00ffff;
      animation: spin 1s linear infinite;
      margin: 0 auto 20px;
    }

    .loading-text {
      color: #00ffff;
      font-size: 18px;
    }

    .notification-toast {
      position: fixed;
      top: 20px;
      right: 20px;
      background: rgba(0, 0, 0, 0.9);
      border: 1px solid #00ffff;
      border-radius: 12px;
      padding: 15px 20px;
      color: #00ffff;
      z-index: 10000;
      display: none;
      animation: slideInRight 0.3s ease;
      box-shadow: 0 4px 20px rgba(0, 255, 255, 0.3);
    }

    @keyframes slideInRight {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .notification-toast.show {
      display: block;
    }

    .quick-actions {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 30px;
    }

    .quick-action-btn {
      padding: 20px;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 16px;
      color: #00ffff;
      cursor: pointer;
      transition: all 0.3s ease;
      text-align: center;
      font-weight: bold;
    }

    .quick-action-btn:hover {
      transform: translateY(-4px);
      background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(168, 85, 247, 0.2));
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.3);
    }

    .quick-action-icon {
      font-size: 32px;
      margin-bottom: 10px;
    }

    .notification-badge {
      position: relative;
    }

    .notification-badge::after {
      content: attr(data-count);
      position: absolute;
      top: -8px;
      right: -8px;
      background: linear-gradient(135deg, #ff006e, #ff4d00);
      color: #fff;
      font-size: 10px;
      font-weight: bold;
      padding: 2px 6px;
      border-radius: 10px;
      min-width: 18px;
      text-align: center;
    }

    .toggle-switch {
      position: relative;
      display: inline-block;
      width: 50px;
      height: 24px;
    }

    .toggle-switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .toggle-slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(255, 255, 255, 0.1);
      transition: 0.4s;
      border-radius: 24px;
      border: 1px solid rgba(0, 255, 255, 0.3);
    }

    .toggle-slider:before {
      position: absolute;
      content: "";
      height: 16px;
      width: 16px;
      left: 4px;
      bottom: 3px;
      background-color: #999;
      transition: 0.4s;
      border-radius: 50%;
    }

    input:checked + .toggle-slider {
      background: linear-gradient(135deg, #00ffff, #a855f7);
    }

    input:checked + .toggle-slider:before {
      transform: translateX(26px);
      background-color: #000;
    }

    .input-with-icon {
      position: relative;
    }

    .input-with-icon input {
      padding-right: 45px;
    }

    .input-icon {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: #00ffff;
      cursor: pointer;
      font-size: 18px;
      transition: all 0.3s ease;
    }

    .input-icon:hover {
      color: #a855f7;
      transform: translateY(-50%) scale(1.2);
    }

    .data-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      overflow-x: auto;
      display: block;
    }

    .data-table thead {
      background: rgba(0, 255, 255, 0.1);
    }

    .data-table th {
      padding: 15px;
      text-align: left;
      color: #00ffff;
      font-weight: bold;
      border-bottom: 2px solid rgba(0, 255, 255, 0.3);
      white-space: nowrap;
    }

    .data-table td {
      padding: 15px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      color: #e0e0e0;
      white-space: nowrap;
    }

    .data-table tr {
      transition: all 0.3s ease;
    }

    .data-table tbody tr:hover {
      background: rgba(0, 255, 255, 0.05);
    }

    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: bold;
      text-transform: uppercase;
    }

    .badge-success {
      background: rgba(0, 255, 136, 0.2);
      color: #00ff88;
      border: 1px solid #00ff88;
    }

    .badge-warning {
      background: rgba(255, 165, 0, 0.2);
      color: #ffa500;
      border: 1px solid #ffa500;
    }

    .badge-danger {
      background: rgba(255, 107, 107, 0.2);
      color: #ff6b6b;
      border: 1px solid #ff6b6b;
    }

    .badge-info {
      background: rgba(0, 255, 255, 0.2);
      color: #00ffff;
      border: 1px solid #00ffff;
    }

    .custom-checkbox {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      user-select: none;
    }

    .custom-checkbox input {
      display: none;
    }

    .checkmark {
      width: 20px;
      height: 20px;
      border: 2px solid #00ffff;
      border-radius: 4px;
      position: relative;
      transition: all 0.3s ease;
    }

    .custom-checkbox input:checked ~ .checkmark {
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border-color: transparent;
    }

    .checkmark::after {
      content: '';
      position: absolute;
      display: none;
      left: 6px;
      top: 2px;
      width: 5px;
      height: 10px;
      border: solid #000;
      border-width: 0 2px 2px 0;
      transform: rotate(45deg);
    }

    .custom-checkbox input:checked ~ .checkmark::after {
      display: block;
    }

    .bulk-actions {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .bulk-action-btn {
      padding: 10px 20px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 10px;
      color: #00ffff;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 14px;
    }

    .bulk-action-btn:hover {
      background: rgba(0, 255, 255, 0.1);
      transform: translateY(-2px);
    }

    .export-import-section {
      display: flex;
      gap: 10px;
      margin-top: 15px;
    }

    .export-btn, .import-btn {
      flex: 1;
      padding: 12px;
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.05);
      color: #00ffff;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: bold;
    }

    .export-btn:hover, .import-btn:hover {
      background: rgba(0, 255, 255, 0.1);
      transform: translateY(-2px);
    }

    .users-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
    }

    .user-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      transition: all 0.3s ease;
    }

    .user-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 255, 255, 0.3);
      border-color: rgba(0, 255, 255, 0.5);
    }

    .user-header {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 15px;
      padding-bottom: 15px;
      border-bottom: 1px solid rgba(0, 255, 255, 0.2);
    }

    .user-avatar {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: bold;
      color: #000;
    }

    .user-info {
      flex: 1;
    }

    .user-name {
      font-size: 18px;
      font-weight: bold;
      color: #00ffff;
      margin-bottom: 5px;
    }

    .user-email {
      font-size: 14px;
      color: #999;
    }

    .user-details {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-bottom: 15px;
    }

    .user-detail-row {
      display: flex;
      justify-content: space-between;
      padding: 8px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 8px;
    }

    .user-detail-label {
      color: #999;
      font-size: 13px;
    }

    .user-detail-value {
      color: #00ffff;
      font-weight: bold;
      font-size: 13px;
    }

    .status-select {
      width: 100%;
      padding: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 8px;
      color: #fff;
      cursor: pointer;
      font-size: 14px;
      margin-bottom: 10px;
    }

    .status-select:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
    }

    .order-status-badge {
      display: inline-block;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      text-transform: uppercase;
    }

    .order-status-badge.pending {
      background: rgba(255, 165, 0, 0.2);
      color: #ffa500;
      border: 1px solid #ffa500;
    }

    .order-status-badge.confirmed {
      background: rgba(0, 255, 136, 0.2);
      color: #00ff88;
      border: 1px solid #00ff88;
    }

    .order-status-badge.processing {
      background: rgba(0, 255, 255, 0.2);
      color: #00ffff;
      border: 1px solid #00ffff;
    }

    .order-status-badge.rejected {
      background: rgba(255, 107, 107, 0.2);
      color: #ff6b6b;
      border: 1px solid #ff6b6b;
    }

    .order-status-badge.maintenance {
      background: rgba(255, 215, 0, 0.2);
      color: #ffd700;
      border: 1px solid #ffd700;
    }

    .table-wrapper {
      overflow-x: auto;
      max-width: 100%;
    }

    /* Screenshot URLs Section */
    .screenshot-urls-section {
      margin-top: 20px;
      padding: 20px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 12px;
      border: 1px solid rgba(0, 255, 255, 0.2);
    }

    .screenshot-url-item {
      display: flex;
      gap: 10px;
      margin-bottom: 10px;
      align-items: center;
    }

    .screenshot-url-input {
      flex: 1;
      padding: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 8px;
      color: #fff;
      font-size: 14px;
    }

    .screenshot-url-input:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
    }

    .screenshot-remove-btn {
      padding: 10px 15px;
      background: rgba(255, 0, 110, 0.2);
      border: 1px solid #ff006e;
      border-radius: 8px;
      color: #ff006e;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 14px;
    }

    .screenshot-remove-btn:hover {
      background: #ff006e;
      color: #fff;
    }

    .screenshot-add-btn {
      width: 100%;
      padding: 10px;
      background: rgba(0, 255, 255, 0.1);
      border: 1px dashed rgba(0, 255, 255, 0.3);
      border-radius: 8px;
      color: #00ffff;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 14px;
      margin-top: 10px;
    }

    .screenshot-add-btn:hover {
      background: rgba(0, 255, 255, 0.2);
      border-style: solid;
    }

    /* User Support Chat Styles */
    .chat-users-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .chat-user-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 15px;
      transition: all 0.3s ease;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .chat-user-card:hover {
      transform: translateX(4px);
      box-shadow: 0 8px 24px rgba(0, 255, 255, 0.3);
      border-color: rgba(0, 255, 255, 0.5);
    }

    .chat-user-info {
      flex: 1;
    }

    .chat-user-name {
      font-size: 16px;
      font-weight: bold;
      color: #00ffff;
      margin-bottom: 5px;
    }

    .chat-user-email {
      font-size: 12px;
      color: #999;
      margin-bottom: 5px;
    }

    .chat-last-message {
      font-size: 13px;
      color: #ccc;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 300px;
    }

    .chat-user-actions {
      display: flex;
      gap: 10px;
    }

    .view-chat-btn {
      padding: 10px 20px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 8px;
      color: #000;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .view-chat-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.5);
    }

    /* Chat Modal Styles */
    .chat-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      backdrop-filter: blur(10px);
      z-index: 10000;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .chat-modal.active {
      display: flex;
    }

    .chat-modal-content {
      background: linear-gradient(180deg, rgba(26, 10, 46, 0.98) 0%, rgba(10, 10, 10, 0.98) 100%);
      backdrop-filter: blur(30px);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 20px;
      width: 100%;
      max-width: 800px;
      height: 80vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 16px 64px rgba(0, 255, 255, 0.3);
    }

    .chat-modal-header {
      padding: 20px;
      border-bottom: 1px solid rgba(0, 255, 255, 0.2);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(0, 255, 255, 0.05);
    }

    .chat-modal-title {
      font-size: 20px;
      font-weight: bold;
      color: #00ffff;
    }

    .chat-modal-close {
      width: 35px;
      height: 35px;
      background: rgba(255, 0, 110, 0.2);
      border: 1px solid #ff006e;
      border-radius: 50%;
      color: #ff006e;
      font-size: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
    }

    .chat-modal-close:hover {
      background: #ff006e;
      color: #fff;
      transform: rotate(90deg);
    }

    .chat-messages-container {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .chat-message {
      display: flex;
      gap: 10px;
      animation: slideInLeft 0.3s ease;
      position: relative;
    }

    .chat-message.admin {
      flex-direction: row-reverse;
      animation: slideInRight 0.3s ease;
    }

    @keyframes slideInLeft {
      from {
        opacity: 0;
        transform: translateX(-30px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    .chat-message-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #000;
      font-weight: bold;
      flex-shrink: 0;
    }

    .chat-message.admin .chat-message-avatar {
      background: linear-gradient(135deg, #a855f7, #ff006e);
    }

    .chat-message-content-wrapper {
      max-width: 70%;
    }

    .chat-message-content {
      padding: 12px 16px;
      border-radius: 16px;
      background: rgba(0, 255, 255, 0.1);
      border: 1px solid rgba(0, 255, 255, 0.3);
      color: #fff;
      line-height: 1.5;
      word-wrap: break-word;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .chat-message-content:hover {
      background: rgba(0, 255, 255, 0.15);
    }

    .chat-message.admin .chat-message-content {
      background: rgba(168, 85, 247, 0.1);
      border-color: rgba(168, 85, 247, 0.3);
    }

    .chat-message.admin .chat-message-content:hover {
      background: rgba(168, 85, 247, 0.15);
    }

    .chat-message-time {
      font-size: 11px;
      color: #999;
      margin-top: 5px;
    }

    .chat-message-actions {
      display: none;
      position: absolute;
      top: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.9);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 8px;
      padding: 5px;
      gap: 5px;
      z-index: 100;
    }

    .chat-message-actions.show {
      display: flex;
    }

    .chat-message-action-btn {
      padding: 5px 10px;
      background: rgba(255, 255, 255, 0.1);
      border: none;
      border-radius: 4px;
      color: #00ffff;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.3s ease;
    }

    .chat-message-action-btn:hover {
      background: rgba(0, 255, 255, 0.2);
    }

    .chat-message-action-btn.delete {
      color: #ff006e;
    }

    .chat-message-action-btn.delete:hover {
      background: rgba(255, 0, 110, 0.2);
    }

    .chat-input-container {
      display: flex;
      gap: 10px;
      padding: 15px;
      background: rgba(255, 255, 255, 0.05);
      border-top: 1px solid rgba(0, 255, 255, 0.2);
    }

    .chat-input {
      flex: 1;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 12px;
      color: #fff;
      font-size: 14px;
      transition: all 0.3s ease;
    }

    .chat-input:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
      background: rgba(255, 255, 255, 0.08);
    }

    .chat-send-btn {
      width: 45px;
      height: 45px;
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border: none;
      border-radius: 12px;
      color: #000;
      font-size: 18px;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .chat-send-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 4px 16px rgba(0, 255, 255, 0.5);
    }

    .chat-send-btn:active {
      transform: scale(0.95);
    }

    .chat-empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #999;
      gap: 10px;
    }

    .chat-empty-icon {
      font-size: 60px;
      opacity: 0.5;
    }

    /* Edit Message Modal */
    .edit-message-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(5px);
      z-index: 10001;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .edit-message-modal.active {
      display: flex;
    }

    .edit-message-content {
      background: rgba(26, 10, 46, 0.98);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 16px;
      padding: 30px;
      width: 100%;
      max-width: 500px;
      box-shadow: 0 8px 32px rgba(0, 255, 255, 0.3);
    }

    .edit-message-title {
      font-size: 20px;
      color: #00ffff;
      margin-bottom: 20px;
      font-weight: bold;
    }

    .edit-message-input {
      width: 100%;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(0, 255, 255, 0.3);
      border-radius: 12px;
      color: #fff;
      font-size: 16px;
      min-height: 100px;
      resize: vertical;
      margin-bottom: 20px;
    }

    .edit-message-input:focus {
      outline: none;
      border-color: #00ffff;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
    }

    .edit-message-actions {
      display: flex;
      gap: 10px;
    }

    .edit-message-actions .btn {
      flex: 1;
    }

    @media (max-width: 768px) {
      .drawer {
        width: min(280px, 85vw);
      }

      .header {
        flex-direction: column;
        text-align: center;
      }

      .products-grid, .coupons-grid, .users-grid {
        grid-template-columns: 1fr;
      }

      .stats-grid {
        grid-template-columns: 1fr;
      }

      .quick-actions {
        grid-template-columns: 1fr;
      }

      .btn-group {
        flex-direction: column;
      }

      .filter-buttons {
        flex-direction: column;
      }

      .filter-btn {
        width: 100%;
      }

      .fab {
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        font-size: 24px;
      }

      .notification-toast {
        right: 10px;
        left: 10px;
        width: auto;
      }

      .data-table {
        font-size: 12px;
      }

      .data-table th,
      .data-table td {
        padding: 8px;
      }

      .chat-modal-content {
        height: 90vh;
        max-width: 100%;
      }

      .chat-message-content-wrapper {
        max-width: 85%;
      }

      .screenshot-url-item {
        flex-direction: column;
      }

      .screenshot-remove-btn {
        width: 100%;
      }
    }

    ::-webkit-scrollbar {
      width: 10px;
      height: 10px;
    }

    ::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, 0.05);
    }

    ::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #00ffff, #a855f7);
      border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: linear-gradient(135deg, #a855f7, #00ffff);
    }

    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    }

    *:focus {
      outline: 2px solid #00ffff;
      outline-offset: 2px;
    }

    button:focus, a:focus, input:focus, select:focus, textarea:focus {
      outline: 2px solid #00ffff;
      outline-offset: 2px;
    }

    .fade-in {
      animation: fadeIn 0.5s ease;
    }

    .slide-up {
      animation: slideUp 0.5s ease;
    }

    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .scale-in {
      animation: scaleIn 0.3s ease;
    }

    @keyframes scaleIn {
      from {
        opacity: 0;
        transform: scale(0.9);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    .pulse {
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }
  </style>
</head>
<body>
  <!-- Loading Overlay -->
  <div class="loading-overlay" id="loadingOverlay">
    <div class="loading-content">
      <div class="loading-spinner-large"></div>
      <div class="loading-text">Loading...</div>
    </div>
  </div>

  <!-- Notification Toast -->
  <div class="notification-toast" id="notificationToast"></div>

  <!-- Drawer Overlay -->
  <div class="drawer-overlay" id="drawerOverlay"></div>

  <!-- Menu Toggle Button -->
  <button class="menu-toggle" id="menuToggle" aria-label="Toggle menu" aria-expanded="false">
    <span></span>
  </button>

  <!-- Drawer -->
  <div class="drawer" id="drawer">
    <div class="drawer-header">
      <button class="drawer-close-btn" id="drawerCloseBtn" aria-label="Close menu">×</button>
      <div class="drawer-brand">
        <img id="drawerLogo" class="drawer-logo" src="" alt="Logo" style="display:none;">
        <div id="drawerBrandName" class="drawer-brand-name">Admin Panel</div>
      </div>
      <div class="drawer-user-info">
        <strong id="drawerUserName">Admin User</strong>
        <span id="drawerUserEmail">admin@example.com</span>
      </div>
    </div>

    <nav class="drawer-nav">
      <div class="drawer-nav-item active" data-tab="dashboard">
        <span class="drawer-nav-icon"><i class="fas fa-tachometer-alt"></i></span>
        <span>Dashboard</span>
      </div>
      <div class="drawer-nav-item" data-tab="brand">
        <span class="drawer-nav-icon"><i class="fas fa-palette"></i></span>
        <span>Brand Settings</span>
      </div>
      <div class="drawer-nav-item" data-tab="contact">
        <span class="drawer-nav-icon"><i class="fas fa-phone"></i></span>
        <span>Contact Settings</span>
      </div>
      <div class="drawer-nav-item" data-tab="products">
        <span class="drawer-nav-icon"><i class="fas fa-box"></i></span>
        <span>Products</span>
      </div>
      <div class="drawer-nav-item" data-tab="orders">
        <span class="drawer-nav-icon"><i class="fas fa-shopping-cart"></i></span>
        <span>Orders</span>
      </div>
      <div class="drawer-nav-item" data-tab="coupons">
        <span class="drawer-nav-icon"><i class="fas fa-ticket-alt"></i></span>
        <span>Coupons</span>
      </div>
      <div class="drawer-nav-item" data-tab="users">
        <span class="drawer-nav-icon"><i class="fas fa-users"></i></span>
        <span>User Management</span>
      </div>
      <div class="drawer-nav-item" data-tab="support">
        <span class="drawer-nav-icon"><i class="fas fa-headset"></i></span>
        <span>User's Support</span>
      </div>
      <div class="drawer-nav-item" data-tab="settings">
        <span class="drawer-nav-icon"><i class="fas fa-cog"></i></span>
        <span>Settings</span>
      </div>
    </nav>

    <div class="drawer-footer">
      <button class="btn" id="drawerLogoutBtn" style="background: linear-gradient(135deg, #ff006e, #ff4d00);">
        <span style="margin-right: 8px;"><i class="fas fa-sign-out-alt"></i></span> Logout
      </button>
    </div>
  </div>

  <!-- Login Screen -->
  <div id="loginScreen" class="login-container" style="display: none;">
    <div class="login-card">
      <h1 class="login-title">Admin Panel</h1>
      <div id="loginError" style="display: none;" class="error-message"></div>
      <div class="input-group">
        <label><i class="fas fa-envelope"></i> Email</label>
        <input type="email" id="loginEmail" placeholder="admin@example.com" autocomplete="email">
      </div>
      <div class="input-group">
        <label><i class="fas fa-lock"></i> Password</label>
        <input type="password" id="loginPassword" placeholder="Enter password" autocomplete="current-password">
      </div>
      <button class="btn" id="loginBtn">Login</button>
    </div>
  </div>

  <!-- Setup Screen -->
  <div id="setupScreen" class="login-container" style="display: none;">
    <div class="login-card">
      <h1 class="login-title"><i class="fas fa-rocket"></i> First Time Setup</h1>
      <p style="text-align: center; color: #00ffff; margin-bottom: 20px; line-height: 1.6;">
        Welcome! No admin account exists yet.<br>
        Create your first admin account to get started.
      </p>
      <div id="setupError" style="display: none;" class="error-message"></div>
      <div class="input-group">
        <label><i class="fas fa-user"></i> Admin Name</label>
        <input type="text" id="setupName" placeholder="Enter your name" autocomplete="name">
      </div>
      <div class="input-group">
        <label><i class="fas fa-envelope"></i> Email</label>
        <input type="email" id="setupEmail" placeholder="admin@example.com" autocomplete="email">
      </div>
      <div class="input-group">
        <label><i class="fas fa-lock"></i> Password (min 8 characters)</label>
        <input type="password" id="setupPassword" placeholder="Create password" autocomplete="new-password">
      </div>
      <div class="input-group">
        <label><i class="fas fa-lock"></i> Confirm Password</label>
        <input type="password" id="setupConfirmPassword" placeholder="Confirm password" autocomplete="new-password">
      </div>
      <button class="btn" id="setupBtn">Create Admin Account</button>
      <p style="text-align: center; color: #999; margin-top: 15px; font-size: 14px;">
        This will be the master admin account
      </p>
    </div>
  </div>

  <!-- Admin Dashboard -->
  <div id="adminDashboard" class="admin-container">
    <div class="header">
      <div class="brand-section">
        <img id="headerLogo" class="brand-logo" src="" alt="Logo" style="display:none;">
        <div id="headerBrandName" class="brand-name">Admin Panel</div>
      </div>
    </div>

    <!-- Dashboard Tab -->
    <div id="dashboardTab" class="tab-content active">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-tachometer-alt"></i> Dashboard Overview</h2>
        
        <!-- Quick Actions -->
        <div class="quick-actions">
          <div class="quick-action-btn" data-action="addProduct">
            <div class="quick-action-icon"><i class="fas fa-plus"></i></div>
            <div>Add Product</div>
          </div>
          <div class="quick-action-btn" data-action="createCoupon">
            <div class="quick-action-icon"><i class="fas fa-ticket-alt"></i></div>
            <div>Create Coupon</div>
          </div>
          <div class="quick-action-btn notification-badge" data-count="0" id="ordersNotification" data-action="viewOrders">
            <div class="quick-action-icon"><i class="fas fa-shopping-cart"></i></div>
            <div>View Orders</div>
          </div>
          <div class="quick-action-btn" data-action="viewUsers">
            <div class="quick-action-icon"><i class="fas fa-users"></i></div>
            <div>Manage Users</div>
          </div>
        </div>

        <!-- Dashboard Stats -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value" id="dashTotalProducts">0</div>
            <div class="stat-label">Total Products</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="dashTotalOrders">0</div>
            <div class="stat-label">Total Orders</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="dashTodayOrders">0</div>
            <div class="stat-label">Today's Orders</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="dashTotalRevenue">$0</div>
            <div class="stat-label">Total Revenue</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="dashTotalUsers">0</div>
            <div class="stat-label">Total Users</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="dashTotalCoupons">0</div>
            <div class="stat-label">Active Coupons</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Brand Settings Tab -->
    <div id="brandTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-palette"></i> Brand Settings</h2>
        <div id="brandSuccess" style="display: none;" class="success-message"></div>
        <div class="input-group">
          <label><i class="fas fa-tag"></i> Brand Name</label>
          <input type="text" id="brandName" placeholder="Enter brand name">
        </div>
        <div class="input-group">
          <label><i class="fas fa-image"></i> Brand Logo URL</label>
          <input type="text" id="brandLogoUrl" placeholder="https://example.com/logo.png">
        </div>
        <div id="brandLogoPreview" style="display: none; margin-top: 15px; text-align: center;">
          <p style="color: #00ffff; margin-bottom: 10px;">Logo Preview:</p>
          <img id="brandLogoPreviewImg" style="max-width: 200px; border-radius: 12px; border: 2px solid #00ffff;" src="" alt="Logo Preview">
        </div>
        <button class="btn" id="saveBrandBtn"><i class="fas fa-save"></i> Save Brand Settings</button>
      </div>
    </div>

    <!-- Contact Settings Tab -->
    <div id="contactTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-phone"></i> Contact Settings</h2>
        <div id="contactSuccess" style="display: none;" class="success-message"></div>
        <div class="input-group">
          <label><i class="fas fa-store"></i> Brand Name</label>
          <input type="text" id="contactBrandName" placeholder="Brand name">
        </div>
        <div class="input-group">
          <label><i class="fas fa-user-tie"></i> Legal Operator</label>
          <input type="text" id="contactOperator" placeholder="Operator name">
        </div>
        <div class="input-group">
          <label><i class="fas fa-envelope"></i> Email</label>
          <input type="email" id="contactEmail" placeholder="contact@example.com">
        </div>
        <div class="input-group">
          <label><i class="fas fa-phone"></i> Phone</label>
          <input type="tel" id="contactPhone" placeholder="+91 1234567890">
        </div>
        <div class="input-group">
          <label><i class="fab fa-youtube"></i> YouTube Link</label>
          <input type="url" id="contactYoutube" placeholder="https://youtube.com/@channel">
        </div>
        <div class="input-group">
          <label><i class="fab fa-telegram"></i> Telegram Link</label>
          <input type="url" id="contactTelegram" placeholder="https://t.me/channel">
        </div>
        <button class="btn" id="saveContactBtn"><i class="fas fa-save"></i> Save Contact Settings</button>
      </div>
    </div>

    <!-- Products Tab -->
    <div id="productsTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-box"></i> Add/Edit Product</h2>
        <div id="productSuccess" style="display: none;" class="success-message"></div>
        <input type="hidden" id="editProductId">
        <div class="input-group">
          <label><i class="fas fa-heading"></i> Product Title</label>
          <input type="text" id="productTitle" placeholder="Product name">
        </div>
        <div class="input-group">
          <label><i class="fas fa-image"></i> Product Image URL</label>
          <input type="text" id="productImageUrl" placeholder="https://example.com/product.jpg">
        </div>
        <div class="input-group">
          <label><i class="fas fa-align-left"></i> Product Description</label>
          <textarea id="productDescription" placeholder="Product description"></textarea>
        </div>
        <div class="input-group">
          <label><i class="fas fa-dollar-sign"></i> Original Price ($)</label>
          <input type="number" id="productRealPrice" placeholder="999" min="0" step="0.01" oninput="updateDiscountPreview()">
        </div>
        <div class="input-group">
          <label><i class="fas fa-tags"></i> Discount (%)</label>
          <input type="number" id="productDiscountPercent" placeholder="50" min="0" max="100" step="0.01" oninput="updateDiscountPreview()">
          <small id="discountPreviewText" style="display: block; margin-top: 5px; color: #00ff88;"></small>
        </div>
        <div class="input-group">
          <label><i class="fas fa-qrcode"></i> QR Code Image URL</label>
          <input type="text" id="productQrImageUrl" placeholder="https://example.com/qr-code.png">
        </div>
        <div class="input-group">
          <label><i class="fas fa-download"></i> Download Link</label>
          <input type="text" id="productDownloadLink" placeholder="https://example.com/download/product.zip">
          <small style="color: #999; font-size: 12px; margin-top: 5px; display: block;">
            This link will be available to users after successful order
          </small>
        </div>

        <!-- Product Screenshots Section -->
        <div class="input-group">
          <label><i class="fas fa-images"></i> Product Screenshots</label>
          <div class="screenshot-urls-section" id="screenshotUrlsSection">
            <div id="screenshotUrlsList"></div>
            <button type="button" class="screenshot-add-btn" id="addScreenshotBtn">
              <i class="fas fa-plus"></i> Add Screenshot URL
            </button>
          </div>
          <small style="color: #999; font-size: 12px; margin-top: 5px; display: block;">
            Add multiple screenshot URLs to showcase your product
          </small>
        </div>

        <button class="btn" id="saveProductBtn"><i class="fas fa-save"></i> Save Product</button>
        <button class="btn" style="margin-top: 10px; background: linear-gradient(135deg, #ff006e, #ff4d00);" id="clearProductBtn"><i class="fas fa-times"></i> Cancel / Clear</button>
      </div>

      <div class="card">
        <h2 class="card-title"><i class="fas fa-boxes"></i> All Products</h2>
        <div class="search-box">
          <input type="text" id="productSearch" placeholder="🔍 Search products...">
        </div>
        <div class="bulk-actions">
          <button class="bulk-action-btn" id="selectAllProducts"><i class="fas fa-check-square"></i> Select All</button>
          <button class="bulk-action-btn" id="deselectAllProducts"><i class="far fa-square"></i> Deselect All</button>
          <button class="bulk-action-btn" id="deleteSelectedProducts" style="background: rgba(255, 0, 110, 0.1); border-color: #ff006e; color: #ff006e;"><i class="fas fa-trash"></i> Delete Selected</button>
        </div>
        <div id="productsGrid" class="products-grid"></div>
      </div>
    </div>

    <!-- Orders Tab -->
    <div id="ordersTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-shopping-cart"></i> All Orders</h2>
        <div class="search-box">
          <input type="text" id="orderSearch" placeholder="🔍 Search orders...">
        </div>
        <div class="filter-buttons">
          <button class="filter-btn active" data-filter="all"><i class="fas fa-calendar"></i> All Time</button>
          <button class="filter-btn" data-filter="today"><i class="fas fa-calendar-day"></i> Today</button>
          <button class="filter-btn" data-filter="week"><i class="fas fa-calendar-week"></i> This Week</button>
          <button class="filter-btn" data-filter="month"><i class="fas fa-calendar-alt"></i> This Month</button>
        </div>
        <div id="ordersList" class="orders-list"></div>
      </div>
    </div>

    <!-- Coupons Tab -->
    <div id="couponsTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-ticket-alt"></i> Create/Edit Coupon</h2>
        <div id="couponSuccess" style="display: none;" class="success-message"></div>
        <input type="hidden" id="editCouponId">
        
        <div class="input-group">
          <label><i class="fas fa-barcode"></i> Coupon Code</label>
          <div class="input-with-icon">
            <input type="text" id="couponCode" placeholder="SAVE50" style="text-transform: uppercase;" maxlength="20">
            <span class="input-icon" id="generateCouponBtn" title="Generate Random Code"><i class="fas fa-dice"></i></span>
          </div>
          <small style="color: #999; font-size: 12px;">Unique code for customers to use</small>
        </div>

        <div class="input-group">
          <label><i class="fas fa-percentage"></i> Discount Type</label>
          <select id="couponDiscountType">
            <option value="percentage">Percentage (%)</option>
            <option value="fixed">Fixed Amount ($)</option>
          </select>
        </div>

        <div class="input-group">
          <label id="couponDiscountLabel"><i class="fas fa-percent"></i> Discount Value (%)</label>
          <input type="number" id="couponDiscountValue" placeholder="10" min="0">
          <small style="color: #999; font-size: 12px;" id="couponDiscountHelp">Enter percentage value (0-100)</small>
        </div>

        <div class="input-group">
          <label><i class="fas fa-dollar-sign"></i> Minimum Purchase Amount ($)</label>
          <input type="number" id="couponMinAmount" placeholder="0" min="0">
          <small style="color: #999; font-size: 12px;">Minimum cart value required (0 for no minimum)</small>
        </div>

        <div class="input-group" id="maxDiscountGroup">
          <label><i class="fas fa-hand-holding-usd"></i> Maximum Discount Cap ($)</label>
          <input type="number" id="couponMaxDiscount" placeholder="0" min="0">
          <small style="color: #999; font-size: 12px;">Maximum discount amount (0 for no cap, only for percentage type)</small>
        </div>

        <div class="input-group">
          <label><i class="fas fa-users"></i> Usage Limit</label>
          <input type="number" id="couponUsageLimit" placeholder="100" min="0">
          <small style="color: #999; font-size: 12px;">How many times this coupon can be used (0 for unlimited)</small>
        </div>

        <div class="input-group">
          <label><i class="fas fa-calendar-times"></i> Expiry Date</label>
          <input type="datetime-local" id="couponExpiryDate">
          <small style="color: #999; font-size: 12px;">Leave empty for no expiry</small>
        </div>

        <div class="input-group">
          <label><i class="fas fa-comment-alt"></i> Description</label>
          <textarea id="couponDescription" placeholder="Get flat 50% off on all products"></textarea>
          <small style="color: #999; font-size: 12px;">Short description for customers</small>
        </div>

        <div class="input-group">
          <label style="display: flex; align-items: center; gap: 10px;">
            <div class="toggle-switch">
              <input type="checkbox" id="couponActive" checked>
              <span class="toggle-slider"></span>
            </div>
            <span><i class="fas fa-toggle-on"></i> Active Status</span>
          </label>
          <small style="color: #999; font-size: 12px;">Toggle to activate/deactivate coupon</small>
        </div>

        <button class="btn" id="saveCouponBtn"><i class="fas fa-save"></i> Save Coupon</button>
        <button class="btn" style="margin-top: 10px; background: linear-gradient(135deg, #ff006e, #ff4d00);" id="clearCouponBtn"><i class="fas fa-times"></i> Cancel / Clear</button>
      </div>

      <div class="card">
        <h2 class="card-title"><i class="fas fa-tickets-alt"></i> All Coupons</h2>
        <div class="search-box">
          <input type="text" id="couponSearch" placeholder="🔍 Search coupons...">
        </div>
        <div class="filter-buttons">
          <button class="filter-btn active" data-coupon-filter="all"><i class="fas fa-list"></i> All</button>
          <button class="filter-btn" data-coupon-filter="active"><i class="fas fa-check-circle"></i> Active</button>
          <button class="filter-btn" data-coupon-filter="inactive"><i class="fas fa-times-circle"></i> Inactive</button>
          <button class="filter-btn" data-coupon-filter="expired"><i class="fas fa-hourglass-end"></i> Expired</button>
        </div>
        <div id="couponsGrid" class="coupons-grid"></div>
      </div>
    </div>

    <!-- User Management Tab -->
    <div id="usersTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-users"></i> User Management</h2>
        <div class="search-box">
          <input type="text" id="userSearch" placeholder="🔍 Search users...">
        </div>
        <div class="stats-grid" style="margin-bottom: 20px;">
          <div class="stat-card">
            <div class="stat-value" id="totalUsersCount">0</div>
            <div class="stat-label">Total Users</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="activeUsersCount">0</div>
            <div class="stat-label">Active Users</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="totalUserOrders">0</div>
            <div class="stat-label">Total User Orders</div>
          </div>
        </div>
        <div id="usersGrid" class="users-grid"></div>
      </div>
    </div>

    <!-- User's Support Tab -->
    <div id="supportTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-headset"></i> User's Support</h2>
        <div class="search-box">
          <input type="text" id="supportSearch" placeholder="🔍 Search users...">
        </div>
        <div id="chatUsersList" class="chat-users-list"></div>
      </div>
    </div>

    <!-- Settings Tab -->
    <div id="settingsTab" class="tab-content">
      <div class="card">
        <h2 class="card-title"><i class="fas fa-cog"></i> Admin Settings</h2>
        <div id="settingsSuccess" style="display: none;" class="success-message"></div>
        
        <div class="input-group">
          <label><i class="fas fa-user-edit"></i> Change Display Name</label>
          <input type="text" id="settingsDisplayName" placeholder="Admin Name">
        </div>

        <button class="btn" id="saveSettingsBtn"><i class="fas fa-save"></i> Save Settings</button>
      </div>

      <div class="card">
        <h2 class="card-title"><i class="fas fa-trash-alt"></i> Danger Zone</h2>
        <p style="color: #ff6b6b; margin-bottom: 20px; line-height: 1.6;">
          <i class="fas fa-exclamation-triangle"></i> Warning: These actions cannot be undone. Please be careful!
        </p>
        
        <button class="btn" style="background: linear-gradient(135deg, #ffa500, #ff8c00); margin-bottom: 10px;" id="clearAllOrdersBtn">
          <i class="fas fa-trash"></i> Clear All Orders
        </button>
        
        <button class="btn" style="background: linear-gradient(135deg, #ff006e, #ff4d00);" id="clearAllDataBtn">
          <i class="fas fa-exclamation-triangle"></i> Clear All Data (Reset Everything)
        </button>
      </div>

      <div class="card">
        <h2 class="card-title"><i class="fas fa-info-circle"></i> System Information</h2>
        <div style="background: rgba(0, 0, 0, 0.3); padding: 20px; border-radius: 12px; border: 1px solid rgba(0, 255, 255, 0.2);">
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #999;"><i class="fas fa-code-branch"></i> Version:</span>
            <span style="color: #00ffff; font-weight: bold;">3.0.0 Premium</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #999;"><i class="fas fa-database"></i> Database:</span>
            <span style="color: #00ffff; font-weight: bold;">Firebase Realtime</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #999;"><i class="fas fa-clock"></i> Last Login:</span>
            <span style="color: #00ffff; font-weight: bold;" id="lastLoginTime">-</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #999;"><i class="fas fa-envelope"></i> Admin Email:</span>
            <span style="color: #00ffff; font-weight: bold;" id="adminEmailDisplay">-</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #999;"><i class="fas fa-key"></i> Admin Password:</span>
            <span style="color: #00ffff; font-weight: bold;" id="adminPasswordDisplay">••••••••</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Chat Modal -->
  <div class="chat-modal" id="chatModal">
    <div class="chat-modal-content">
      <div class="chat-modal-header">
        <div class="chat-modal-title" id="chatModalTitle">
          <i class="fas fa-comments"></i> Chat with User
        </div>
        <div class="chat-modal-close" id="chatModalClose">×</div>
      </div>
      <div class="chat-messages-container" id="chatMessagesContainer">
        <div class="chat-empty-state">
          <div class="chat-empty-icon">💬</div>
          <div>No messages yet</div>
        </div>
      </div>
      <div class="chat-input-container">
        <input type="text" class="chat-input" id="chatInput" placeholder="Type your message..." maxlength="500">
        <button class="chat-send-btn" id="chatSendBtn">
          <i class="fas fa-paper-plane"></i>
        </button>
      </div>
    </div>
  </div>

  <!-- Edit Message Modal -->
  <div class="edit-message-modal" id="editMessageModal">
    <div class="edit-message-content">
      <div class="edit-message-title"><i class="fas fa-edit"></i> Edit Message</div>
      <textarea class="edit-message-input" id="editMessageInput" placeholder="Edit your message..."></textarea>
      <div class="edit-message-actions">
        <button class="btn" style="background: linear-gradient(135deg, #ff006e, #ff4d00);" id="cancelEditBtn">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button class="btn" id="saveEditBtn">
          <i class="fas fa-check"></i> Save
        </button>
      </div>
    </div>
  </div>

  <!-- Floating Action Button -->
  <button class="fab" id="fab" style="display: none;" title="Scroll to Top">
    <i class="fas fa-arrow-up"></i>
  </button>

  <!-- Firebase SDK -->
  <script type="module">
    import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js';
    import { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged, createUserWithEmailAndPassword, updateProfile } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js';
    import { getDatabase, ref, set, get, push, remove, onValue, update, off } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-database.js';

    const firebaseConfig = {
    apiKey: "AIzaSyBY19bfyTxQKV9qp_mGAPhJOVpUgy-v6R8",
  authDomain: "cipher-pro-store.firebaseapp.com",
  databaseURL: "https://cipher-pro-store-default-rtdb.firebaseio.com",
  projectId: "cipher-pro-store",
  storageBucket: "cipher-pro-store.firebasestorage.app",
  messagingSenderId: "445639151152",
  appId: "1:445639151152:web:93cbca2068849284cd67f5",
  measurementId: "G-BZRH898NCH"
};

    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const db = getDatabase(app);

    window.auth = auth;
    window.db = db;
    window.dbRef = ref;
    window.dbSet = set;
    window.dbGet = get;
    window.dbPush = push;
    window.dbRemove = remove;
    window.dbOnValue = onValue;
    window.dbUpdate = update;
    window.dbOff = off;
    window.signInWithEmailAndPassword = signInWithEmailAndPassword;
    window.signOut = signOut;
    window.createUserWithEmailAndPassword = createUserWithEmailAndPassword;
    window.updateProfile = updateProfile;

    let activeListeners = [];

    function showLoadingOverlay(text = 'Loading...') {
      const overlay = document.getElementById('loadingOverlay');
      const loadingText = overlay.querySelector('.loading-text');
      loadingText.textContent = text;
      overlay.classList.add('active');
    }

    function hideLoadingOverlay() {
      document.getElementById('loadingOverlay').classList.remove('active');
    }

    function showNotification(message, duration = 3000) {
      const toast = document.getElementById('notificationToast');
      toast.textContent = message;
      toast.classList.add('show');
      setTimeout(() => {
        toast.classList.remove('show');
      }, duration);
    }

    async function checkAdminSetup() {
      try {
        showLoadingOverlay('Checking admin setup...');
        
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Connection timeout')), 10000)
        );
        
        const dataPromise = get(ref(db, 'meta/adminSetup/completed'));
        const snapshot = await Promise.race([dataPromise, timeoutPromise]);
        
        hideLoadingOverlay();
        
        if (snapshot.exists() && snapshot.val() === true) {
          document.getElementById('setupScreen').style.display = 'none';
          document.getElementById('loginScreen').style.display = 'flex';
          document.getElementById('menuToggle').classList.add('hidden');
        } else {
          document.getElementById('setupScreen').style.display = 'flex';
          document.getElementById('loginScreen').style.display = 'none';
          document.getElementById('menuToggle').classList.add('hidden');
        }
      } catch (error) {
        console.error('Error checking admin setup:', error);
        hideLoadingOverlay();
        document.getElementById('setupScreen').style.display = 'flex';
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('menuToggle').classList.add('hidden');
      }
    }

    function setupRealtimeListeners() {
      cleanupListeners();

      const productsListener = onValue(ref(db, 'products'), () => {
        loadProducts();
        updateStats();
      });
      activeListeners.push({ ref: ref(db, 'products'), unsubscribe: productsListener });

      const ordersListener = onValue(ref(db, 'orders'), () => {
        loadOrders();
        updateStats();
        updateOrderNotification();
      });
      activeListeners.push({ ref: ref(db, 'orders'), unsubscribe: ordersListener });

      const couponsListener = onValue(ref(db, 'coupons'), () => {
        loadCoupons();
        updateStats();
      });
      activeListeners.push({ ref: ref(db, 'coupons'), unsubscribe: couponsListener });

      const brandListener = onValue(ref(db, 'meta/brand'), () => {
        loadBrandSettings();
      });
      activeListeners.push({ ref: ref(db, 'meta/brand'), unsubscribe: brandListener });

      const usersListener = onValue(ref(db, 'users'), () => {
        loadUsers();
        updateStats();
      });
      activeListeners.push({ ref: ref(db, 'users'), unsubscribe: usersListener });

      const chatsListener = onValue(ref(db, 'chats'), () => {
        loadChatUsers();
      });
      activeListeners.push({ ref: ref(db, 'chats'), unsubscribe: chatsListener });
    }

    function cleanupListeners() {
      activeListeners.forEach(listener => {
        off(listener.ref);
      });
      activeListeners = [];
    }

    onAuthStateChanged(auth, (user) => {
      if (user) {
        hideLoadingOverlay();
        document.getElementById('setupScreen').style.display = 'none';
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('adminDashboard').style.display = 'block';
        document.getElementById('fab').style.display = 'flex';
        document.getElementById('menuToggle').classList.remove('hidden');
        
        const displayName = user.displayName || 'Admin User';
        document.getElementById('drawerUserName').textContent = displayName;
        document.getElementById('drawerUserEmail').textContent = user.email;
        
        document.getElementById('lastLoginTime').textContent = new Date().toLocaleString('en-IN');
        document.getElementById('adminEmailDisplay').textContent = user.email;
        document.getElementById('settingsDisplayName').value = displayName;
        
        loadBrandSettings();
        loadContactSettings();
        loadProducts();
        loadOrders();
        loadCoupons();
        loadUsers();
        loadChatUsers();
        updateStats();
        setupRealtimeListeners();
        
        showNotification('✅ Welcome back, ' + displayName + '!');
      } else {
        document.getElementById('adminDashboard').style.display = 'none';
        document.getElementById('fab').style.display = 'none';
        document.getElementById('menuToggle').classList.add('hidden');
        cleanupListeners();
        checkAdminSetup();
      }
    });

    window.setupRealtimeListeners = setupRealtimeListeners;
    window.cleanupListeners = cleanupListeners;
    window.showLoadingOverlay = showLoadingOverlay;
    window.hideLoadingOverlay = hideLoadingOverlay;
    window.showNotification = showNotification;
  </script>

  <script>
    const MESSAGE_DISPLAY_DURATION = 5000;
    const ITEMS_PER_PAGE = 20;

    let allProducts = [];
    let allOrders = [];
    let allCoupons = [];
    let allUsers = [];
    let allChatUsers = [];
    let currentOrderFilter = 'all';
    let currentCouponFilter = 'all';
    let selectedProducts = new Set();
    let screenshotUrls = [];
    let currentChatUserId = null;
    let currentChatMessages = [];
    let currentEditMessageId = null;
    let longPressTimer = null;

    function escapeHtml(text) {
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    function isValidEmail(email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    }

    function isValidPhone(phone) {
      const phoneRegex = /^[\d\s\+\-\(\)]+$/;
      return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
    }

    function isValidUrl(string) {
      try {
        new URL(string);
        return true;
      } catch (_) {
        return false;
      }
    }

    function showMessage(elementId, message, type = 'success') {
      const element = document.getElementById(elementId);
      element.textContent = message;
      element.className = type === 'success' ? 'success-message' : 'error-message';
      element.style.display = 'block';
      setTimeout(() => {
        element.style.display = 'none';
      }, MESSAGE_DISPLAY_DURATION);
    }

    function debounce(func, delay) {
      let timeoutId;
      return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
      };
    }

    function formatCurrency(amount) {
      const value = parseFloat(amount);
      if (value === 0) return 'FREE';
      return '$' + value.toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      });
    }

    function formatDate(dateString) {
      return new Date(dateString).toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }

    function toggleDrawer() {
      const drawer = document.getElementById('drawer');
      const overlay = document.getElementById('drawerOverlay');
      const toggle = document.getElementById('menuToggle');
      
      const isActive = drawer.classList.toggle('active');
      overlay.classList.toggle('active');
      toggle.classList.toggle('active');
      toggle.setAttribute('aria-expanded', isActive);
      
      document.body.style.overflow = isActive ? 'hidden' : '';
    }

    function switchTabFromDrawer(tabName) {
      const tabContent = document.getElementById(tabName + 'Tab');
      if (!tabContent) return;

      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
      });

      tabContent.classList.add('active');

      document.querySelectorAll('.drawer-nav-item').forEach(item => {
        item.classList.remove('active');
      });
      const navItem = document.querySelector(`.drawer-nav-item[data-tab="${tabName}"]`);
      if (navItem) navItem.classList.add('active');

      const drawer = document.getElementById('drawer');
      if (drawer && drawer.classList.contains('active')) {
        toggleDrawer();
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    document.getElementById('menuToggle')?.addEventListener('click', toggleDrawer);
    document.getElementById('drawerCloseBtn')?.addEventListener('click', toggleDrawer);
    document.getElementById('drawerOverlay')?.addEventListener('click', toggleDrawer);

    document.querySelectorAll('.drawer-nav-item').forEach(item => {
      item.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        switchTabFromDrawer(tabName);
      });
    });

    document.getElementById('drawerLogoutBtn')?.addEventListener('click', logout);

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const drawer = document.getElementById('drawer');
        if (drawer.classList.contains('active')) {
          toggleDrawer();
        }
        
        const chatModal = document.getElementById('chatModal');
        if (chatModal.classList.contains('active')) {
          closeChatModal();
        }

        const editModal = document.getElementById('editMessageModal');
        if (editModal.classList.contains('active')) {
          closeEditMessageModal();
        }
      }
    });

    async function setupAdmin() {
      const name = document.getElementById('setupName').value.trim();
      const email = document.getElementById('setupEmail').value.trim();
      const password = document.getElementById('setupPassword').value.trim();
      const confirmPassword = document.getElementById('setupConfirmPassword').value.trim();

      document.getElementById('setupError').style.display = 'none';

      if (!name || !email || !password || !confirmPassword) {
        showMessage('setupError', 'Please fill all fields', 'error');
        return;
      }

      if (!isValidEmail(email)) {
        showMessage('setupError', 'Please enter a valid email address', 'error');
        return;
      }

      if (password.length < 8) {
        showMessage('setupError', 'Password must be at least 8 characters', 'error');
        return;
      }

      if (password !== confirmPassword) {
        showMessage('setupError', 'Passwords do not match', 'error');
        return;
      }

      const btn = document.getElementById('setupBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span>Creating Account...';

      try {
        const userCredential = await window.createUserWithEmailAndPassword(window.auth, email, password);
        
        await window.updateProfile(userCredential.user, {
          displayName: name
        });

        await window.dbSet(window.dbRef(window.db, 'meta/adminSetup'), {
          completed: true,
          adminEmail: email,
          adminName: name,
          adminPassword: password,
          setupDate: new Date().toISOString()
        });

        showMessage('setupError', 'Admin account created successfully!', 'success');
        
        document.getElementById('setupName').value = '';
        document.getElementById('setupEmail').value = '';
        document.getElementById('setupPassword').value = '';
        document.getElementById('setupConfirmPassword').value = '';
        
      } catch (error) {
        let errorMsg = 'Setup failed: ';
        switch(error.code) {
          case 'auth/email-already-in-use':
            errorMsg += 'This email is already registered';
            break;
          case 'auth/invalid-email':
            errorMsg += 'Invalid email format';
            break;
          case 'auth/weak-password':
            errorMsg += 'Password is too weak';
            break;
          default:
            errorMsg += error.message;
        }
        showMessage('setupError', errorMsg, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = 'Create Admin Account';
      }
    }

    document.getElementById('setupBtn')?.addEventListener('click', setupAdmin);

    async function login() {
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value.trim();

      document.getElementById('loginError').style.display = 'none';

      if (!email || !password) {
        showMessage('loginError', 'Please enter email and password', 'error');
        return;
      }

      if (!isValidEmail(email)) {
        showMessage('loginError', 'Please enter a valid email address', 'error');
        return;
      }

      const btn = document.getElementById('loginBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span>Logging in...';

      try {
        await window.signInWithEmailAndPassword(window.auth, email, password);
      } catch (error) {
        let errorMsg = 'Login failed: ';
        switch(error.code) {
          case 'auth/user-not-found':
            errorMsg += 'No account found with this email';
            break;
          case 'auth/wrong-password':
            errorMsg += 'Incorrect password';
            break;
          case 'auth/invalid-email':
            errorMsg += 'Invalid email format';
            break;
          case 'auth/too-many-requests':
            errorMsg += 'Too many failed attempts. Please try again later';
            break;
          default:
            errorMsg += error.message;
        }
        showMessage('loginError', errorMsg, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = 'Login';
      }
    }

    document.getElementById('loginBtn')?.addEventListener('click', login);

    ['loginEmail', 'loginPassword'].forEach(id => {
      document.getElementById(id)?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          login();
        }
      });
    });

    async function logout() {
      if (confirm('Are you sure you want to logout?')) {
        try {
          window.showLoadingOverlay('Logging out...');
          window.cleanupListeners();
          await window.signOut(window.auth);
          window.hideLoadingOverlay();
        } catch (error) {
          window.hideLoadingOverlay();
          alert('Logout failed: ' + error.message);
        }
      }
    }

    function updateOrderNotification() {
      const today = new Date().toDateString();
      const todayOrders = allOrders.filter(order => 
        new Date(order.createdAt).toDateString() === today
      ).length;
      
      const notification = document.getElementById('ordersNotification');
      if (todayOrders > 0) {
        notification.setAttribute('data-count', todayOrders);
      } else {
        notification.setAttribute('data-count', '0');
      }
    }

    async function updateStats() {
      try {
        const productsSnapshot = await window.dbGet(window.dbRef(window.db, 'products'));
        const totalProducts = productsSnapshot.exists() ? Object.keys(productsSnapshot.val()).length : 0;
        document.getElementById('dashTotalProducts').textContent = totalProducts;

        const ordersSnapshot = await window.dbGet(window.dbRef(window.db, 'orders'));
        let totalOrders = 0;
        let todayOrders = 0;
        let totalRevenue = 0;
        
        if (ordersSnapshot.exists()) {
          const orders = ordersSnapshot.val();
          totalOrders = Object.keys(orders).length;
          
          const today = new Date().toDateString();
          
          Object.values(orders).forEach(order => {
            const orderDate = new Date(order.createdAt).toDateString();
            if (orderDate === today) {
              todayOrders++;
            }
            const price = parseFloat(order.finalAmount || order.productSnapshot?.discountedPrice || 0);
            if (!isNaN(price)) {
              totalRevenue += price;
            }
          });
        }

        document.getElementById('dashTotalOrders').textContent = totalOrders;
        document.getElementById('dashTodayOrders').textContent = todayOrders;
        document.getElementById('dashTotalRevenue').textContent = formatCurrency(totalRevenue);

        const usersSnapshot = await window.dbGet(window.dbRef(window.db, 'users'));
        const totalUsers = usersSnapshot.exists() ? Object.keys(usersSnapshot.val()).length : 0;
        document.getElementById('dashTotalUsers').textContent = totalUsers;

        const couponsSnapshot = await window.dbGet(window.dbRef(window.db, 'coupons'));
        let activeCoupons = 0;
        
        if (couponsSnapshot.exists()) {
          const coupons = couponsSnapshot.val();
          const now = Date.now();
          activeCoupons = Object.values(coupons).filter(coupon => 
            coupon.isActive && (!coupon.expiryDate || new Date(coupon.expiryDate).getTime() > now)
          ).length;
        }

        document.getElementById('dashTotalCoupons').textContent = activeCoupons;

        const adminSetupSnapshot = await window.dbGet(window.dbRef(window.db, 'meta/adminSetup'));
        if (adminSetupSnapshot.exists()) {
          const adminData = adminSetupSnapshot.val();
          if (adminData.adminPassword) {
            document.getElementById('adminPasswordDisplay').textContent = adminData.adminPassword;
          }
        }
        
      } catch (error) {
        console.error('Error updating stats:', error);
      }
    }

    async function loadBrandSettings() {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, 'meta/brand'));
        if (snapshot.exists()) {
          const data = snapshot.val();
          document.getElementById('brandName').value = data.name || '';
          document.getElementById('brandLogoUrl').value = data.logoUrl || '';
          
          if (data.logoUrl && isValidUrl(data.logoUrl)) {
            document.getElementById('headerLogo').src = data.logoUrl;
            document.getElementById('headerLogo').style.display = 'block';
            document.getElementById('drawerLogo').src = data.logoUrl;
            document.getElementById('drawerLogo').style.display = 'block';
            document.getElementById('brandLogoPreview').style.display = 'block';
            document.getElementById('brandLogoPreviewImg').src = data.logoUrl;
          }
          if (data.name) {
            document.getElementById('headerBrandName').textContent = escapeHtml(data.name);
            document.getElementById('drawerBrandName').textContent = escapeHtml(data.name);
          }
        }
      } catch (error) {
        console.error('Error loading brand settings:', error);
      }
    }

    async function saveBrandSettings() {
      const name = document.getElementById('brandName').value.trim();
      const logoUrl = document.getElementById('brandLogoUrl').value.trim();

      if (!name) {
        showMessage('brandSuccess', 'Please enter brand name', 'error');
        return;
      }

      if (logoUrl && !isValidUrl(logoUrl)) {
        showMessage('brandSuccess', 'Please enter a valid logo URL', 'error');
        return;
      }

      const btn = document.getElementById('saveBrandBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span>Saving...';

      try {
        await window.dbSet(window.dbRef(window.db, 'meta/brand'), {
          name: name,
          logoUrl: logoUrl,
          updatedAt: new Date().toISOString()
        });
        showMessage('brandSuccess', 'Brand settings saved successfully!', 'success');
        loadBrandSettings();
      } catch (error) {
        showMessage('brandSuccess', 'Error saving brand settings: ' + error.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Brand Settings';
      }
    }

    document.getElementById('saveBrandBtn')?.addEventListener('click', saveBrandSettings);

    document.getElementById('brandLogoUrl')?.addEventListener('input', function() {
      const url = this.value.trim();
      if (url && isValidUrl(url)) {
        document.getElementById('brandLogoPreview').style.display = 'block';
        document.getElementById('brandLogoPreviewImg').src = url;
        document.getElementById('brandLogoPreviewImg').onerror = function() {
          this.src = 'about:blank';
          this.alt = 'Invalid image URL';
        };
      } else {
        document.getElementById('brandLogoPreview').style.display = 'none';
      }
    });

    async function loadContactSettings() {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, 'meta/contact'));
        if (snapshot.exists()) {
          const data = snapshot.val();
          document.getElementById('contactBrandName').value = data.brandName || '';
          document.getElementById('contactOperator').value = data.operator || '';
          document.getElementById('contactEmail').value = data.email || '';
          document.getElementById('contactPhone').value = data.phone || '';
          document.getElementById('contactYoutube').value = data.socialYoutube || '';
          document.getElementById('contactTelegram').value = data.socialTelegram || '';
        }
      } catch (error) {
        console.error('Error loading contact settings:', error);
      }
    }

    async function saveContactSettings() {
      const email = document.getElementById('contactEmail').value.trim();
      const phone = document.getElementById('contactPhone').value.trim();
      const youtube = document.getElementById('contactYoutube').value.trim();
      const telegram = document.getElementById('contactTelegram').value.trim();

      if (email && !isValidEmail(email)) {
        showMessage('contactSuccess', 'Please enter a valid email address', 'error');
        return;
      }

      if (phone && !isValidPhone(phone)) {
        showMessage('contactSuccess', 'Please enter a valid phone number', 'error');
        return;
      }

      if (youtube && !isValidUrl(youtube)) {
        showMessage('contactSuccess', 'Please enter a valid YouTube URL', 'error');
        return;
      }

      if (telegram && !isValidUrl(telegram)) {
        showMessage('contactSuccess', 'Please enter a valid Telegram URL', 'error');
        return;
      }

      const btn = document.getElementById('saveContactBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span>Saving...';

      try {
        await window.dbSet(window.dbRef(window.db, 'meta/contact'), {
          brandName: document.getElementById('contactBrandName').value.trim(),
          operator: document.getElementById('contactOperator').value.trim(),
          email: email,
          phone: phone,
          socialYoutube: youtube,
          socialTelegram: telegram,
          updatedAt: new Date().toISOString()
        });
        showMessage('contactSuccess', 'Contact settings saved successfully!', 'success');
      } catch (error) {
        showMessage('contactSuccess', 'Error saving contact settings: ' + error.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Contact Settings';
      }
    }

    document.getElementById('saveContactBtn')?.addEventListener('click', saveContactSettings);

    // Screenshot URLs Management
    function renderScreenshotUrls() {
      const list = document.getElementById('screenshotUrlsList');
      list.innerHTML = '';

      screenshotUrls.forEach((url, index) => {
        const item = document.createElement('div');
        item.className = 'screenshot-url-item';
        item.innerHTML = `
          <input type="text" class="screenshot-url-input" value="${escapeHtml(url)}" 
                 placeholder="https://example.com/screenshot${index + 1}.png" 
                 data-index="${index}">
          <button type="button" class="screenshot-remove-btn" data-index="${index}">
            <i class="fas fa-times"></i> Remove
          </button>
        `;
        list.appendChild(item);
      });

      list.querySelectorAll('.screenshot-url-input').forEach(input => {
        input.addEventListener('input', function() {
          const index = parseInt(this.dataset.index);
          screenshotUrls[index] = this.value.trim();
        });
      });

      list.querySelectorAll('.screenshot-remove-btn').forEach(btn => {
        btn.addEventListener('click', function() {
          const index = parseInt(this.dataset.index);
          screenshotUrls.splice(index, 1);
          renderScreenshotUrls();
        });
      });
    }

    document.getElementById('addScreenshotBtn')?.addEventListener('click', function() {
      screenshotUrls.push('');
      renderScreenshotUrls();
    });

    async function loadProducts() {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, 'products'));
        const grid = document.getElementById('productsGrid');
        grid.innerHTML = '';

        if (snapshot.exists()) {
          const products = snapshot.val();
          allProducts = Object.keys(products).map(key => ({
            id: key,
            ...products[key]
          })).sort((a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0));
          
          displayProducts(allProducts);
        } else {
          grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-box"></i></div><div class="empty-state-title">No Products Found</div><div class="empty-state-text">Add your first product to get started!</div></div>';
        }
      } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('productsGrid').innerHTML = '<p style="color: #ff6b6b; text-align: center; padding: 40px;">Error loading products. Please refresh the page.</p>';
      }
    }

    function displayProducts(products) {
      const grid = document.getElementById('productsGrid');
      grid.innerHTML = '';
      
      if (products.length === 0) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-search"></i></div><div class="empty-state-title">No Products Found</div><div class="empty-state-text">No products match your search criteria.</div></div>';
        return;
      }

      products.forEach(product => {
        const card = createProductCard(product.id, product);
        grid.appendChild(card);
      });
    }

    const filterProducts = debounce(function() {
      const searchTerm = document.getElementById('productSearch').value.toLowerCase().trim();
      
      if (!searchTerm) {
        displayProducts(allProducts);
        return;
      }

      const filtered = allProducts.filter(product => 
        product.title.toLowerCase().includes(searchTerm) ||
        (product.description && product.description.toLowerCase().includes(searchTerm))
      );

      displayProducts(filtered);
    }, 300);

    document.getElementById('productSearch')?.addEventListener('input', filterProducts);

    function createProductCard(id, product) {
      const card = document.createElement('div');
      card.className = 'product-card';
      
      const isSelected = selectedProducts.has(id);
      
      const screenshotCount = product.screenshots && Array.isArray(product.screenshots) ? product.screenshots.length : 0;
      
      const isFree = parseFloat(product.discountedPrice) === 0;
      const priceDisplay = isFree ? 
        `<span class="price-discount" style="font-size: 24px;">FREE</span>` :
        `<span class="price-original">${formatCurrency(product.realPrice)}</span>
         <span class="price-discount">${formatCurrency(product.discountedPrice)}</span>`;
      
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
          <label class="custom-checkbox">
            <input type="checkbox" class="product-checkbox" data-id="${id}" ${isSelected ? 'checked' : ''}>
            <span class="checkmark"></span>
            <span>Select</span>
          </label>
        </div>
        <img src="${escapeHtml(product.imageUrl)}" alt="${escapeHtml(product.title)}" class="product-image" loading="lazy" onerror="if(this.src!=='about:blank'){this.src='about:blank';this.alt='Image failed'}">
        <div class="product-title">${escapeHtml(product.title)}</div>
        <div class="product-price">
          ${priceDisplay}
        </div>
        ${product.downloadLink ? '<div style="color: #00ff88; font-size: 12px; margin-bottom: 5px;"><i class="fas fa-download"></i> Download link available</div>' : ''}
        ${screenshotCount > 0 ? `<div style="color: #00ffff; font-size: 12px; margin-bottom: 10px;"><i class="fas fa-images"></i> ${screenshotCount} Screenshot(s)</div>` : ''}
        <div class="btn-group">
          <button class="btn-small btn-edit" data-edit-id="${id}"><i class="fas fa-edit"></i> Edit</button>
          <button class="btn-small btn-delete" data-delete-id="${id}"><i class="fas fa-trash"></i> Delete</button>
        </div>
      `;
      
      const checkbox = card.querySelector('.product-checkbox');
      checkbox.addEventListener('change', function() {
        if (this.checked) {
          selectedProducts.add(id);
        } else {
          selectedProducts.delete(id);
        }
      });
      
      const editBtn = card.querySelector('[data-edit-id]');
      editBtn.addEventListener('click', () => editProduct(id));
      
      const deleteBtn = card.querySelector('[data-delete-id]');
      deleteBtn.addEventListener('click', () => deleteProduct(id));
      
      return card;
    }

    function updateDiscountPreview() {
      const previewText = document.getElementById('discountPreviewText');
      if (!previewText) return;

      const realPrice = parseFloat(document.getElementById('productRealPrice').value);
      const discountPercent = parseFloat(document.getElementById('productDiscountPercent').value);

      if (isNaN(realPrice) || realPrice < 0 || isNaN(discountPercent) || discountPercent < 0 || discountPercent > 100) {
        previewText.textContent = '';
        return;
      }

      const finalPrice = realPrice - (realPrice * discountPercent / 100);
      previewText.textContent = `Final price: ${formatCurrency(finalPrice)}`;
    }

    async function saveProduct() {
      const productId = document.getElementById('editProductId').value;
      const title = document.getElementById('productTitle').value.trim();
      const imageUrl = document.getElementById('productImageUrl').value.trim();
      const description = document.getElementById('productDescription').value.trim();
      const realPrice = parseFloat(document.getElementById('productRealPrice').value);
      const discountPercent = parseFloat(document.getElementById('productDiscountPercent').value);
      const qrImageUrl = document.getElementById('productQrImageUrl').value.trim();
      const downloadLink = document.getElementById('productDownloadLink').value.trim();

      if (!title || !imageUrl || !description) {
        showMessage('productSuccess', 'Please fill all required fields', 'error');
        return;
      }

      if (!isValidUrl(imageUrl)) {
        showMessage('productSuccess', 'Please enter a valid image URL', 'error');
        return;
      }

      if (qrImageUrl && !isValidUrl(qrImageUrl)) {
        showMessage('productSuccess', 'Please enter a valid QR code URL', 'error');
        return;
      }

      if (downloadLink && !isValidUrl(downloadLink)) {
        showMessage('productSuccess', 'Please enter a valid download link URL', 'error');
        return;
      }

      if (isNaN(realPrice) || realPrice < 0) {
        showMessage('productSuccess', 'Please enter a valid original price', 'error');
        return;
      }

      if (isNaN(discountPercent) || discountPercent < 0 || discountPercent > 100) {
        showMessage('productSuccess', 'Please enter a valid discount percentage (0-100)', 'error');
        return;
      }

      const discountedPrice = realPrice - (realPrice * discountPercent / 100);

      // Validate screenshot URLs
      const validScreenshots = screenshotUrls.filter(url => {
        const trimmed = url.trim();
        return trimmed && isValidUrl(trimmed);
      });

      const productData = {
        title: title,
        imageUrl: imageUrl,
        description: description,
        realPrice: realPrice,
        discountedPrice: discountedPrice,
        qrImageUrl: qrImageUrl,
        downloadLink: downloadLink,
        screenshots: validScreenshots,
        updatedAt: new Date().toISOString()
      };

      if (!productId) {
        productData.createdAt = new Date().toISOString();
      }

      const btn = document.getElementById('saveProductBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span>Saving...';

      try {
        if (productId) {
          await window.dbUpdate(window.dbRef(window.db, `products/${productId}`), productData);
          showMessage('productSuccess', '✅ Product updated successfully!', 'success');
        } else {
          const newRef = window.dbPush(window.dbRef(window.db, 'products'));
          await window.dbSet(newRef, productData);
          showMessage('productSuccess', '✅ Product added successfully!', 'success');
        }
        
        clearProductForm();
        loadProducts();
        window.showNotification('✅ Product saved successfully!');
      } catch (error) {
        showMessage('productSuccess', 'Error saving product: ' + error.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Product';
      }
    }

    document.getElementById('saveProductBtn')?.addEventListener('click', saveProduct);

    async function editProduct(id) {
  try {
    window.showLoadingOverlay('Loading product...');
    const snapshot = await window.dbGet(window.dbRef(window.db, `products/${id}`));
    if (snapshot.exists()) {
      const product = snapshot.val();
      
      // Close drawer if open (with null check)
      const drawer = document.getElementById('drawer');
      if (drawer && drawer.classList.contains('active')) {
        toggleDrawer();
      }
      
      // Switch to products tab
      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
      });
      document.getElementById('productsTab').classList.add('active');
      
      document.querySelectorAll('.drawer-nav-item').forEach(item => {
        item.classList.remove('active');
      });
      const productsNavItem = document.querySelector('[data-tab="products"]');
      if (productsNavItem) {
        productsNavItem.classList.add('active');
      }
      
      // Set values
      document.getElementById('editProductId').value = id;
      document.getElementById('productTitle').value = product.title;
      document.getElementById('productImageUrl').value = product.imageUrl;
      document.getElementById('productDescription').value = product.description;
      document.getElementById('productRealPrice').value = product.realPrice;
      const backCalculatedPercent = product.realPrice > 0
        ? Math.round(((product.realPrice - product.discountedPrice) / product.realPrice) * 10000) / 100
        : 0;
      document.getElementById('productDiscountPercent').value = backCalculatedPercent;
      document.getElementById('productQrImageUrl').value = product.qrImageUrl || '';
      document.getElementById('productDownloadLink').value = product.downloadLink || '';
      
      screenshotUrls = product.screenshots || [];
      renderScreenshotUrls();
      updateDiscountPreview();
      
      document.getElementById('saveProductBtn').innerHTML = '<i class="fas fa-edit"></i> Update Product';
      
      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    window.hideLoadingOverlay();
  } catch (error) {
    window.hideLoadingOverlay();
    alert('Error loading product: ' + error.message);
  }
}

    async function deleteProduct(id) {
      if (confirm('⚠️ Are you sure you want to delete this product? This action cannot be undone.')) {
        try {
          window.showLoadingOverlay('Deleting product...');
          const snapshot = await window.dbGet(window.dbRef(window.db, `products/${id}`));
          const productTitle = snapshot.exists() ? snapshot.val().title : 'Unknown';
          
          await window.dbRemove(window.dbRef(window.db, `products/${id}`));
          showMessage('productSuccess', '🗑️ Product deleted successfully!', 'success');
          loadProducts();
          window.hideLoadingOverlay();
          window.showNotification('🗑️ Product deleted!');
        } catch (error) {
          window.hideLoadingOverlay();
          alert('Error deleting product: ' + error.message);
        }
      }
    }

    function clearProductForm() {
      document.getElementById('editProductId').value = '';
      document.getElementById('productTitle').value = '';
      document.getElementById('productImageUrl').value = '';
      document.getElementById('productDescription').value = '';
      document.getElementById('productRealPrice').value = '';
      document.getElementById('productDiscountPercent').value = '';
      document.getElementById('productQrImageUrl').value = '';
      document.getElementById('productDownloadLink').value = '';
      screenshotUrls = [];
      renderScreenshotUrls();
      const previewText = document.getElementById('discountPreviewText');
      if (previewText) previewText.textContent = '';
      document.getElementById('saveProductBtn').innerHTML = '<i class="fas fa-save"></i> Save Product';
    }

    document.getElementById('clearProductBtn')?.addEventListener('click', clearProductForm);

    document.getElementById('selectAllProducts')?.addEventListener('click', function() {
      document.querySelectorAll('.product-checkbox').forEach(checkbox => {
        checkbox.checked = true;
        selectedProducts.add(checkbox.dataset.id);
      });
    });

    document.getElementById('deselectAllProducts')?.addEventListener('click', function() {
      document.querySelectorAll('.product-checkbox').forEach(checkbox => {
        checkbox.checked = false;
      });
      selectedProducts.clear();
    });

    document.getElementById('deleteSelectedProducts')?.addEventListener('click', async function() {
      if (selectedProducts.size === 0) {
        alert('Please select products to delete');
        return;
      }

      if (confirm(`⚠️ Are you sure you want to delete ${selectedProducts.size} selected product(s)? This action cannot be undone.`)) {
        try {
          window.showLoadingOverlay(`Deleting ${selectedProducts.size} products...`);
          
          for (const id of selectedProducts) {
            await window.dbRemove(window.dbRef(window.db, `products/${id}`));
          }
          
          const count = selectedProducts.size;
          selectedProducts.clear();
          loadProducts();
          window.hideLoadingOverlay();
          window.showNotification(`✅ ${count} products deleted!`);
        } catch (error) {
          window.hideLoadingOverlay();
          alert('Error deleting products: ' + error.message);
        }
      }
    });

    async function loadOrders() {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, 'orders'));
        const list = document.getElementById('ordersList');
        list.innerHTML = '';

        if (snapshot.exists()) {
          const orders = snapshot.val();
          allOrders = Object.keys(orders).map(key => ({
            id: key,
            ...orders[key]
          })).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
          
          filterOrdersByDate(currentOrderFilter);
        } else {
          list.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-shopping-cart"></i></div><div class="empty-state-title">No Orders Yet</div><div class="empty-state-text">Orders will appear here once customers start purchasing.</div></div>';
        }
      } catch (error) {
        console.error('Error loading orders:', error);
        document.getElementById('ordersList').innerHTML = '<p style="color: #ff6b6b; text-align: center; padding: 40px;">Error loading orders. Please refresh the page.</p>';
      }
    }

    function filterOrdersByDate(filter) {
      currentOrderFilter = filter;

      let filtered = allOrders;
      const now = new Date();

      if (filter === 'today') {
        const today = now.toDateString();
        filtered = allOrders.filter(order => 
          new Date(order.createdAt).toDateString() === today
        );
      } else if (filter === 'week') {
        const weekAgo = new Date(now);
        weekAgo.setDate(weekAgo.getDate() - 7);
        filtered = allOrders.filter(order => 
          new Date(order.createdAt) >= weekAgo
        );
      } else if (filter === 'month') {
        const monthAgo = new Date(now);
        monthAgo.setDate(monthAgo.getDate() - 30);
        filtered = allOrders.filter(order => 
          new Date(order.createdAt) >= monthAgo
        );
      }

      displayOrders(filtered);
    }

    document.querySelectorAll('.filter-buttons [data-filter]').forEach(btn => {
      btn.addEventListener('click', function() {
        document.querySelectorAll('.filter-buttons [data-filter]').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        filterOrdersByDate(this.dataset.filter);
      });
    });

    const filterOrders = debounce(function() {
      const searchTerm = document.getElementById('orderSearch').value.toLowerCase().trim();
      
      let filtered = allOrders;

      const now = new Date();
      if (currentOrderFilter === 'today') {
        const today = now.toDateString();
        filtered = filtered.filter(order => 
          new Date(order.createdAt).toDateString() === today
        );
      } else if (currentOrderFilter === 'week') {
        const weekAgo = new Date(now);
        weekAgo.setDate(weekAgo.getDate() - 7);
        filtered = filtered.filter(order => 
          new Date(order.createdAt) >= weekAgo
        );
      } else if (currentOrderFilter === 'month') {
        const monthAgo = new Date(now);
        monthAgo.setDate(monthAgo.getDate() - 30);
        filtered = filtered.filter(order => 
          new Date(order.createdAt) >= monthAgo
        );
      }

      if (searchTerm) {
        filtered = filtered.filter(order => 
          order.id.toLowerCase().includes(searchTerm) ||
          (order.productSnapshot?.title && order.productSnapshot.title.toLowerCase().includes(searchTerm)) ||
          (order.userInput?.name && order.userInput.name.toLowerCase().includes(searchTerm)) ||
          (order.userInput?.utrId && order.userInput.utrId.toLowerCase().includes(searchTerm))
        );
      }

      displayOrders(filtered);
    }, 300);

    document.getElementById('orderSearch')?.addEventListener('input', filterOrders);

    function displayOrders(orders) {
      const list = document.getElementById('ordersList');
      list.innerHTML = '';

      if (orders.length === 0) {
        list.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-search"></i></div><div class="empty-state-title">No Orders Found</div><div class="empty-state-text">No orders match your search or filter criteria.</div></div>';
        return;
      }

      orders.forEach(order => {
        const card = createOrderCard(order.id, order);
        list.appendChild(card);
      });
    }

    function createOrderCard(id, order) {
      const card = document.createElement('div');
      card.className = 'order-card';
      
      const date = formatDate(order.createdAt);
      const status = order.status || 'pending';
      
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
          <div style="color: #a855f7; font-weight: bold;"><i class="fas fa-box"></i> Order ID: ${escapeHtml(id.substring(0, 10))}...</div>
          <div style="color: #00ff88; font-size: 12px;"><i class="fas fa-clock"></i> ${date}</div>
        </div>
        <div class="order-info">
          <div><span class="order-field">Product:</span> <span class="order-value">${escapeHtml(order.productSnapshot?.title || 'N/A')}</span></div>
          <div><span class="order-field">Customer:</span> <span class="order-value">${escapeHtml(order.userInput?.name || 'N/A')}</span></div>
          <div><span class="order-field">UTR ID:</span> <span class="order-value">${escapeHtml(order.userInput?.utrId || 'N/A')}</span></div>
          <div><span class="order-field">Price:</span> <span class="order-value" style="color: #00ff88;">${formatCurrency(order.finalAmount || order.productSnapshot?.discountedPrice || 0)}</span></div>
          ${order.couponUsed ? `<div><span class="order-field">Coupon:</span> <span class="order-value" style="color: #ffa500;">${escapeHtml(order.couponUsed)} (+${formatCurrency(order.discountAmount || 0)})</span></div>` : ''}
        </div>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(0, 255, 255, 0.2);">
          <label style="color: #00ffff; font-size: 14px; margin-bottom: 8px; display: block;"><i class="fas fa-info-circle"></i> Order Status:</label>
          <select class="status-select" data-order-id="${id}" onchange="updateOrderStatus('${id}', this.value)">
            <option value="pending" ${status === 'pending' ? 'selected' : ''}>⏳ Pending</option>
            <option value="confirmed" ${status === 'confirmed' ? 'selected' : ''}>✅ Successful/Confirmed</option>
            <option value="processing" ${status === 'processing' ? 'selected' : ''}>🔄 Processing</option>
            <option value="rejected" ${status === 'rejected' ? 'selected' : ''}>❌ Rejected</option>
            <option value="maintenance" ${status === 'maintenance' ? 'selected' : ''}>🔧 Maintenance</option>
          </select>
          <button class="btn" style="margin-top: 10px; background: linear-gradient(135deg, #ff006e, #ff4d00);" onclick="deleteOrder('${id}')">
            <i class="fas fa-trash"></i> Delete Order
          </button>
        </div>
      `;
      return card;
    }

    async function updateOrderStatus(orderId, newStatus) {
      try {
        window.showLoadingOverlay('Updating order status...');
        
        await window.dbUpdate(window.dbRef(window.db, `orders/${orderId}`), {
          status: newStatus,
          statusUpdatedAt: new Date().toISOString()
        });
        
        window.hideLoadingOverlay();
        window.showNotification(`✅ Order status updated to: ${newStatus}`);
        loadOrders();
      } catch (error) {
        window.hideLoadingOverlay();
        alert('Error updating order status: ' + error.message);
      }
    }

    async function deleteOrder(orderId) {
      if (confirm('⚠️ Are you sure you want to delete this order? This action cannot be undone.')) {
        try {
          window.showLoadingOverlay('Deleting order...');
          
          await window.dbRemove(window.dbRef(window.db, `orders/${orderId}`));
          
          window.hideLoadingOverlay();
          window.showNotification('🗑️ Order deleted successfully!');
          loadOrders();
          updateStats();
        } catch (error) {
          window.hideLoadingOverlay();
          alert('Error deleting order: ' + error.message);
        }
      }
    }

    window.updateOrderStatus = updateOrderStatus;
    window.deleteOrder = deleteOrder;

    function generateCouponCode() {
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
      let code = '';
      for (let i = 0; i < 8; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      document.getElementById('couponCode').value = code;
    }

    document.getElementById('generateCouponBtn')?.addEventListener('click', generateCouponCode);

    function updateDiscountInput() {
      const type = document.getElementById('couponDiscountType').value;
      const label = document.getElementById('couponDiscountLabel');
      const help = document.getElementById('couponDiscountHelp');
      const maxDiscountGroup = document.getElementById('maxDiscountGroup');
      
      if (type === 'percentage') {
        label.innerHTML = '<i class="fas fa-percent"></i> Discount Value (%)';
        help.textContent = 'Enter percentage value (0-100)';
        maxDiscountGroup.style.display = 'block';
      } else {
        label.innerHTML = '<i class="fas fa-dollar-sign"></i> Discount Value ($)';
        help.textContent = 'Enter fixed discount amount in dollars';
        maxDiscountGroup.style.display = 'none';
      }
    }

    document.getElementById('couponDiscountType')?.addEventListener('change', updateDiscountInput);

    async function loadCoupons() {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, 'coupons'));
        const grid = document.getElementById('couponsGrid');
        grid.innerHTML = '';

        if (snapshot.exists()) {
          const coupons = snapshot.val();
          allCoupons = Object.keys(coupons).map(key => ({
            id: key,
            ...coupons[key]
          })).sort((a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0));
          
          filterCouponsByStatus(currentCouponFilter);
        } else {
          grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-ticket-alt"></i></div><div class="empty-state-title">No Coupons Found</div><div class="empty-state-text">Create your first coupon to offer discounts!</div></div>';
        }
      } catch (error) {
        console.error('Error loading coupons:', error);
        document.getElementById('couponsGrid').innerHTML = '<p style="color: #ff6b6b; text-align: center; padding: 40px;">Error loading coupons. Please refresh the page.</p>';
      }
    }

    function filterCouponsByStatus(status) {
      currentCouponFilter = status;

      let filtered = allCoupons;
      const now = Date.now();

      if (status === 'active') {
        filtered = allCoupons.filter(coupon => 
          coupon.isActive && (!coupon.expiryDate || new Date(coupon.expiryDate).getTime() > now)
        );
      } else if (status === 'inactive') {
        filtered = allCoupons.filter(coupon => !coupon.isActive);
      } else if (status === 'expired') {
        filtered = allCoupons.filter(coupon => 
          coupon.expiryDate && new Date(coupon.expiryDate).getTime() <= now
        );
      }

      displayCoupons(filtered);
    }

    document.querySelectorAll('.filter-buttons [data-coupon-filter]').forEach(btn => {
      btn.addEventListener('click', function() {
        this.parentElement.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        filterCouponsByStatus(this.dataset.couponFilter);
      });
    });

    const filterCoupons = debounce(function() {
      const searchTerm = document.getElementById('couponSearch').value.toLowerCase().trim();
      
      let filtered = allCoupons;
      const now = Date.now();

      if (currentCouponFilter === 'active') {
        filtered = filtered.filter(coupon => 
          coupon.isActive && (!coupon.expiryDate || new Date(coupon.expiryDate).getTime() > now)
        );
      } else if (currentCouponFilter === 'inactive') {
        filtered = filtered.filter(coupon => !coupon.isActive);
      } else if (currentCouponFilter === 'expired') {
        filtered = filtered.filter(coupon => 
          coupon.expiryDate && new Date(coupon.expiryDate).getTime() <= now
        );
      }

      if (searchTerm) {
        filtered = filtered.filter(coupon => 
          coupon.code.toLowerCase().includes(searchTerm) ||
          (coupon.description && coupon.description.toLowerCase().includes(searchTerm))
        );
      }

      displayCoupons(filtered);
    }, 300);

    document.getElementById('couponSearch')?.addEventListener('input', filterCoupons);

    function displayCoupons(coupons) {
      const grid = document.getElementById('couponsGrid');
      grid.innerHTML = '';

      if (coupons.length === 0) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-search"></i></div><div class="empty-state-title">No Coupons Found</div><div class="empty-state-text">No coupons match your search or filter criteria.</div></div>';
        return;
      }

      coupons.forEach(coupon => {
        const card = createCouponCard(coupon.id, coupon);
        grid.appendChild(card);
      });
    }

    function createCouponCard(id, coupon) {
      const card = document.createElement('div');
      card.className = 'coupon-card';
      
      const now = Date.now();
      const isExpired = coupon.expiryDate && new Date(coupon.expiryDate).getTime() <= now;
      const statusClass = isExpired ? 'expired' : (coupon.isActive ? 'active' : 'inactive');
      const statusText = isExpired ? 'Expired' : (coupon.isActive ? 'Active' : 'Inactive');
      
      const discountText = coupon.discountType === 'percentage' 
        ? `${coupon.discountValue}% OFF`
        : `$${coupon.discountValue} OFF`;
      
      const expiryText = coupon.expiryDate 
        ? new Date(coupon.expiryDate).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })
        : 'No Expiry';
      
      const usedCount = coupon.usedCount || 0;
      const usageLimit = coupon.usageLimit || 'Unlimited';
      
      card.innerHTML = `
        <div class="coupon-status ${statusClass}">${statusText}</div>
        <div class="coupon-code">${escapeHtml(coupon.code)}</div>
        <div class="coupon-discount">${discountText}</div>
        <div class="coupon-description">${escapeHtml(coupon.description || 'No description')}</div>
        <div class="coupon-details">
          <div class="coupon-detail-item">
            <span class="coupon-detail-label">Min Purchase:</span>
            <span class="coupon-detail-value">${formatCurrency(coupon.minAmount || 0)}</span>
          </div>
          ${coupon.discountType === 'percentage' && coupon.maxDiscount > 0 ? `
          <div class="coupon-detail-item">
            <span class="coupon-detail-label">Max Discount:</span>
            <span class="coupon-detail-value">${formatCurrency(coupon.maxDiscount)}</span>
          </div>
          ` : ''}
          <div class="coupon-detail-item">
            <span class="coupon-detail-label">Used:</span>
            <span class="coupon-detail-value">${usedCount} / ${usageLimit}</span>
          </div>
          <div class="coupon-detail-item">
            <span class="coupon-detail-label">Expires:</span>
            <span class="coupon-detail-value">${expiryText}</span>
          </div>
        </div>
        <div class="btn-group">
          <button class="btn-small" style="background: linear-gradient(135deg, #00ffff, #a855f7); color: #000;" data-copy-code="${escapeHtml(coupon.code)}"><i class="fas fa-copy"></i> Copy</button>
          <button class="btn-small btn-edit" data-edit-coupon="${id}"><i class="fas fa-edit"></i> Edit</button>
          <button class="btn-small btn-delete" data-delete-coupon="${id}"><i class="fas fa-trash"></i> Delete</button>
        </div>
      `;

      const copyBtn = card.querySelector('[data-copy-code]');
      copyBtn.addEventListener('click', function() {
        copyCouponCode(this.dataset.copyCode);
      });

      const editBtn = card.querySelector('[data-edit-coupon]');
      editBtn.addEventListener('click', () => editCoupon(id));

      const deleteBtn = card.querySelector('[data-delete-coupon]');
      deleteBtn.addEventListener('click', () => deleteCoupon(id));

      return card;
    }

    function copyCouponCode(code) {
      navigator.clipboard.writeText(code).then(() => {
        window.showNotification(`✅ Coupon code "${code}" copied!`);
      }).catch(err => {
        alert('Failed to copy: ' + err);
      });
    }

    async function saveCoupon() {
      const couponId = document.getElementById('editCouponId').value;
      const code = document.getElementById('couponCode').value.trim().toUpperCase();
      const discountType = document.getElementById('couponDiscountType').value;
      const discountValue = parseFloat(document.getElementById('couponDiscountValue').value);
      const minAmount = parseFloat(document.getElementById('couponMinAmount').value) || 0;
      const maxDiscount = parseFloat(document.getElementById('couponMaxDiscount').value) || 0;
      const usageLimit = parseInt(document.getElementById('couponUsageLimit').value) || 0;
      const expiryDate = document.getElementById('couponExpiryDate').value;
      const description = document.getElementById('couponDescription').value.trim();
      const isActive = document.getElementById('couponActive').checked;

      if (!code) {
        showMessage('couponSuccess', 'Please enter a coupon code', 'error');
        return;
      }

      if (code.length < 4) {
        showMessage('couponSuccess', 'Coupon code must be at least 4 characters', 'error');
        return;
      }

      if (isNaN(discountValue) || discountValue <= 0) {
        showMessage('couponSuccess', 'Please enter a valid discount value', 'error');
        return;
      }

      if (discountType === 'percentage' && discountValue > 100) {
        showMessage('couponSuccess', 'Percentage discount cannot exceed 100%', 'error');
        return;
      }

      if (!couponId) {
        const existingCoupon = allCoupons.find(c => c.code === code);
        if (existingCoupon) {
          showMessage('couponSuccess', 'A coupon with this code already exists', 'error');
          return;
        }
      } else {
        const existingCoupon = allCoupons.find(c => c.code === code && c.id !== couponId);
        if (existingCoupon) {
          showMessage('couponSuccess', 'A coupon with this code already exists', 'error');
          return;
        }
      }

      const couponData = {
        code: code,
        discountType: discountType,
        discountValue: discountValue,
        minAmount: minAmount,
        maxDiscount: maxDiscount,
        usageLimit: usageLimit,
        expiryDate: expiryDate || null,
        description: description,
        isActive: isActive,
        updatedAt: new Date().toISOString()
      };

      if (!couponId) {
        couponData.createdAt = new Date().toISOString();
        couponData.usedCount = 0;
      }

      const btn = document.getElementById('saveCouponBtn');
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span>Saving...';

      try {
        if (couponId) {
          const existingSnapshot = await window.dbGet(window.dbRef(window.db, `coupons/${couponId}`));
          if (existingSnapshot.exists()) {
            couponData.usedCount = existingSnapshot.val().usedCount || 0;
            couponData.createdAt = existingSnapshot.val().createdAt;
          }
          await window.dbUpdate(window.dbRef(window.db, `coupons/${couponId}`), couponData);
          showMessage('couponSuccess', '✅ Coupon updated successfully!', 'success');
        } else {
          const newRef = window.dbPush(window.dbRef(window.db, 'coupons'));
          await window.dbSet(newRef, couponData);
          showMessage('couponSuccess', '✅ Coupon created successfully!', 'success');
        }
        
        clearCouponForm();
        loadCoupons();
        window.showNotification('✅ Coupon saved successfully!');
      } catch (error) {
        showMessage('couponSuccess', 'Error saving coupon: ' + error.message, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Coupon';
      }
    }

    document.getElementById('saveCouponBtn')?.addEventListener('click', saveCoupon);

    async function editCoupon(id) {
      try {
        window.showLoadingOverlay('Loading coupon...');
        const snapshot = await window.dbGet(window.dbRef(window.db, `coupons/${id}`));
        if (snapshot.exists()) {
          const coupon = snapshot.val();
          document.getElementById('editCouponId').value = id;
          document.getElementById('couponCode').value = coupon.code;
          document.getElementById('couponDiscountType').value = coupon.discountType;
          document.getElementById('couponDiscountValue').value = coupon.discountValue;
          document.getElementById('couponMinAmount').value = coupon.minAmount || 0;
          document.getElementById('couponMaxDiscount').value = coupon.maxDiscount || 0;
          document.getElementById('couponUsageLimit').value = coupon.usageLimit || 0;
          document.getElementById('couponExpiryDate').value = coupon.expiryDate || '';
          document.getElementById('couponDescription').value = coupon.description || '';
          document.getElementById('couponActive').checked = coupon.isActive;
          
          updateDiscountInput();
          document.getElementById('saveCouponBtn').innerHTML = '<i class="fas fa-edit"></i> Update Coupon';
          
          switchTabFromDrawer('coupons');
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        window.hideLoadingOverlay();
      } catch (error) {
        window.hideLoadingOverlay();
        alert('Error loading coupon: ' + error.message);
      }
    }

    async function deleteCoupon(id) {
      if (confirm('⚠️ Are you sure you want to delete this coupon? This action cannot be undone.')) {
        try {
          window.showLoadingOverlay('Deleting coupon...');
          const snapshot = await window.dbGet(window.dbRef(window.db, `coupons/${id}`));
          const couponCode = snapshot.exists() ? snapshot.val().code : 'Unknown';
          
          await window.dbRemove(window.dbRef(window.db, `coupons/${id}`));
          showMessage('couponSuccess', '🗑️ Coupon deleted successfully!', 'success');
          loadCoupons();
          window.hideLoadingOverlay();
          window.showNotification('🗑️ Coupon deleted!');
        } catch (error) {
          window.hideLoadingOverlay();
          alert('Error deleting coupon: ' + error.message);
        }
      }
    }

    function clearCouponForm() {
      document.getElementById('editCouponId').value = '';
      document.getElementById('couponCode').value = '';
      document.getElementById('couponDiscountType').value = 'percentage';
      document.getElementById('couponDiscountValue').value = '';
      document.getElementById('couponMinAmount').value = '';
      document.getElementById('couponMaxDiscount').value = '';
      document.getElementById('couponUsageLimit').value = '';
      document.getElementById('couponExpiryDate').value = '';
      document.getElementById('couponDescription').value = '';
      document.getElementById('couponActive').checked = true;
      updateDiscountInput();
      document.getElementById('saveCouponBtn').innerHTML = '<i class="fas fa-save"></i> Save Coupon';
    }

    document.getElementById('clearCouponBtn')?.addEventListener('click', clearCouponForm);

    async function loadUsers() {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, 'users'));
        const grid = document.getElementById('usersGrid');
        grid.innerHTML = '';

        if (snapshot.exists()) {
          const users = snapshot.val();
          allUsers = Object.keys(users).map(key => ({
            id: key,
            ...users[key]
          }));
          
          displayUsers(allUsers);
          updateUserStats();
        } else {
          grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-users"></i></div><div class="empty-state-title">No Users Found</div><div class="empty-state-text">Users will appear here once they sign up.</div></div>';
        }
      } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('usersGrid').innerHTML = '<p style="color: #ff6b6b; text-align: center; padding: 40px;">Error loading users. Please refresh the page.</p>';
      }
    }

    function displayUsers(users) {
      const grid = document.getElementById('usersGrid');
      grid.innerHTML = '';

      if (users.length === 0) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-search"></i></div><div class="empty-state-title">No Users Found</div><div class="empty-state-text">No users match your search criteria.</div></div>';
        return;
      }

      users.forEach(user => {
        const card = createUserCard(user.id, user);
        grid.appendChild(card);
      });
    }

    async function updateUserStats() {
      try {
        document.getElementById('totalUsersCount').textContent = allUsers.length;
        
        let activeUsers = 0;
        let totalUserOrders = 0;

        for (const user of allUsers) {
          if (user.purchases) {
            activeUsers++;
            totalUserOrders += Object.keys(user.purchases).length;
          }
        }

        document.getElementById('activeUsersCount').textContent = activeUsers;
        document.getElementById('totalUserOrders').textContent = totalUserOrders;
      } catch (error) {
        console.error('Error updating user stats:', error);
      }
    }

    const filterUsers = debounce(function() {
      const searchTerm = document.getElementById('userSearch').value.toLowerCase().trim();
      
      if (!searchTerm) {
        displayUsers(allUsers);
        return;
      }

      const filtered = allUsers.filter(user => 
        (user.profile?.name && user.profile.name.toLowerCase().includes(searchTerm)) ||
        (user.profile?.email && user.profile.email.toLowerCase().includes(searchTerm)) ||
        user.id.toLowerCase().includes(searchTerm)
      );

      displayUsers(filtered);
    }, 300);

    document.getElementById('userSearch')?.addEventListener('input', filterUsers);

    function createUserCard(userId, userData) {
      const card = document.createElement('div');
      card.className = 'user-card';
      
      const userName = userData.profile?.name || 'Unknown User';
      const userEmail = userData.profile?.email || 'No email';
      const userInitial = userName.charAt(0).toUpperCase();
      
      const purchaseCount = userData.purchases ? Object.keys(userData.purchases).length : 0;
      const bookmarkCount = userData.bookmarks ? Object.keys(userData.bookmarks).length : 0;
      const joinedDate = userData.profile?.createdAt 
        ? new Date(userData.profile.createdAt).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })
        : 'Unknown';

      card.innerHTML = `
        <div class="user-header">
          <div class="user-avatar">${userInitial}</div>
          <div class="user-info">
            <div class="user-name">${escapeHtml(userName)}</div>
            <div class="user-email">${escapeHtml(userEmail)}</div>
          </div>
        </div>
        <div class="user-details">
          <div class="user-detail-row">
            <span class="user-detail-label"><i class="fas fa-shopping-bag"></i> Purchases:</span>
            <span class="user-detail-value">${purchaseCount}</span>
          </div>
          <div class="user-detail-row">
            <span class="user-detail-label"><i class="fas fa-bookmark"></i> Bookmarks:</span>
            <span class="user-detail-value">${bookmarkCount}</span>
          </div>
          <div class="user-detail-row">
            <span class="user-detail-label"><i class="fas fa-calendar"></i> Joined:</span>
            <span class="user-detail-value">${joinedDate}</span>
          </div>
          <div class="user-detail-row">
            <span class="user-detail-label"><i class="fas fa-id-card"></i> User ID:</span>
            <span class="user-detail-value" style="font-size: 11px; word-break: break-all;">${userId.substring(0, 20)}...</span>
          </div>
        </div>
        <div class="btn-group">
          <button class="btn-small btn-edit" onclick="viewUserDetails('${userId}')"><i class="fas fa-eye"></i> View Details</button>
          <button class="btn-small btn-delete" onclick="deleteUser('${userId}')"><i class="fas fa-trash"></i> Delete</button>
        </div>
      `;

      return card;
    }

    async function viewUserDetails(userId) {
      try {
        window.showLoadingOverlay('Loading user details...');
        const snapshot = await window.dbGet(window.dbRef(window.db, `users/${userId}`));
        
        if (snapshot.exists()) {
          const userData = snapshot.val();
          const userName = userData.profile?.name || 'Unknown User';
          const userEmail = userData.profile?.email || 'No email';
          
          let detailsHtml = `
            <h3 style="color: #00ffff; margin-bottom: 20px;"><i class="fas fa-user"></i> User Details</h3>
            <div style="background: rgba(0, 0, 0, 0.3); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
              <p style="margin-bottom: 10px;"><strong style="color: #00ffff;">Name:</strong> ${escapeHtml(userName)}</p>
              <p style="margin-bottom: 10px;"><strong style="color: #00ffff;">Email:</strong> ${escapeHtml(userEmail)}</p>
              <p style="margin-bottom: 10px;"><strong style="color: #00ffff;">User ID:</strong> <span style="font-size: 12px; word-break: break-all;">${userId}</span></p>
            </div>
          `;

          if (userData.purchases) {
            const purchases = Object.entries(userData.purchases);
            detailsHtml += `<h4 style="color: #00ffff; margin-bottom: 15px;"><i class="fas fa-shopping-bag"></i> Purchases (${purchases.length})</h4>`;
            
            for (const [purchaseId, purchase] of purchases) {
              const orderSnapshot = await window.dbGet(window.dbRef(window.db, `orders/${purchase.orderId}`));
              if (orderSnapshot.exists()) {
                const order = orderSnapshot.val();
                detailsHtml += `
                  <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(0, 255, 255, 0.2);">
                    <p style="color: #a855f7; font-weight: bold; margin-bottom: 5px;">${escapeHtml(order.productSnapshot?.title || 'Unknown Product')}</p>
                    <p style="font-size: 12px; color: #999;">Purchased: ${formatDate(purchase.purchasedAt)}</p>
                    <p style="font-size: 12px; color: #00ff88;">Amount: ${formatCurrency(order.finalAmount || order.productSnapshot?.discountedPrice || 0)}</p>
                  </div>
                `;
              }
            }
          }

          if (userData.bookmarks) {
            const bookmarks = Object.entries(userData.bookmarks);
            detailsHtml += `<h4 style="color: #00ffff; margin: 20px 0 15px 0;"><i class="fas fa-bookmark"></i> Bookmarks (${bookmarks.length})</h4>`;
            
            for (const [bookmarkId, bookmark] of bookmarks) {
              const productSnapshot = await window.dbGet(window.dbRef(window.db, `products/${bookmark.productId}`));
              if (productSnapshot.exists()) {
                const product = productSnapshot.val();
                detailsHtml += `
                  <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(168, 85, 247, 0.2);">
                    <p style="color: #a855f7; font-weight: bold;">${escapeHtml(product.title)}</p>
                  </div>
                `;
              }
            }
          }

          window.hideLoadingOverlay();
          
          const modal = document.createElement('div');
          modal.className = 'modal active';
          modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
              <span class="modal-close" onclick="this.parentElement.parentElement.remove(); document.body.style.overflow = '';">×</span>
              ${detailsHtml}
              <button class="btn" style="margin-top: 20px;" onclick="this.parentElement.parentElement.remove(); document.body.style.overflow = '';"><i class="fas fa-times"></i> Close</button>
            </div>
          `;
          document.body.appendChild(modal);
          document.body.style.overflow = 'hidden';
        }
      } catch (error) {
        window.hideLoadingOverlay();
        alert('Error loading user details: ' + error.message);
      }
    }

    async function deleteUser(userId) {
      if (confirm('⚠️ Are you sure you want to delete this user? This will also delete all their purchases and bookmarks. This action cannot be undone.')) {
        try {
          window.showLoadingOverlay('Deleting user...');
          
          await window.dbRemove(window.dbRef(window.db, `users/${userId}`));
          
          window.hideLoadingOverlay();
          window.showNotification('🗑️ User deleted successfully!');
          loadUsers();
        } catch (error) {
          window.hideLoadingOverlay();
          alert('Error deleting user: ' + error.message);
        }
      }
    }

    window.viewUserDetails = viewUserDetails;
    window.deleteUser = deleteUser;

    // User's Support Chat Functions
    async function loadChatUsers() {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, 'chats'));
        const list = document.getElementById('chatUsersList');
        list.innerHTML = '';

        if (snapshot.exists()) {
          const chats = snapshot.val();
          allChatUsers = Object.keys(chats).map(key => ({
            userId: key,
            ...chats[key].info
          })).sort((a, b) => new Date(b.lastMessageTime || 0) - new Date(a.lastMessageTime || 0));
          
          displayChatUsers(allChatUsers);
        } else {
          list.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-headset"></i></div><div class="empty-state-title">No Support Requests</div><div class="empty-state-text">Users will appear here when they contact support.</div></div>';
        }
      } catch (error) {
        console.error('Error loading chat users:', error);
        document.getElementById('chatUsersList').innerHTML = '<p style="color: #ff6b6b; text-align: center; padding: 40px;">Error loading support chats. Please refresh the page.</p>';
      }
    }

    function displayChatUsers(users) {
      const list = document.getElementById('chatUsersList');
      list.innerHTML = '';

      if (users.length === 0) {
        list.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-search"></i></div><div class="empty-state-title">No Users Found</div><div class="empty-state-text">No users match your search criteria.</div></div>';
        return;
      }

      users.forEach(user => {
        const card = createChatUserCard(user);
        list.appendChild(card);
      });
    }

    const filterChatUsers = debounce(function() {
      const searchTerm = document.getElementById('supportSearch').value.toLowerCase().trim();
      
      if (!searchTerm) {
        displayChatUsers(allChatUsers);
        return;
      }

      const filtered = allChatUsers.filter(user => 
        (user.userName && user.userName.toLowerCase().includes(searchTerm)) ||
        (user.userEmail && user.userEmail.toLowerCase().includes(searchTerm))
      );

      displayChatUsers(filtered);
    }, 300);

    document.getElementById('supportSearch')?.addEventListener('input', filterChatUsers);

    function createChatUserCard(user) {
      const card = document.createElement('div');
      card.className = 'chat-user-card';
      
      const userName = user.userName || 'Unknown User';
      const userEmail = user.userEmail || 'No email';
      const lastMessage = user.lastMessage || 'No messages yet';
      const lastMessageTime = user.lastMessageTime ? formatDate(user.lastMessageTime) : '';

      card.innerHTML = `
        <div class="chat-user-info">
          <div class="chat-user-name">${escapeHtml(userName)}</div>
          <div class="chat-user-email">${escapeHtml(userEmail)}</div>
          <div class="chat-last-message">💬 ${escapeHtml(lastMessage)}</div>
          ${lastMessageTime ? `<div style="font-size: 11px; color: #666; margin-top: 3px;"><i class="far fa-clock"></i> ${lastMessageTime}</div>` : ''}
        </div>
        <div class="chat-user-actions">
          <button class="view-chat-btn" onclick="openChatWithUser('${user.userId}', '${escapeHtml(userName)}')">
            <i class="fas fa-comments"></i> View
          </button>
        </div>
      `;

      return card;
    }

    async function openChatWithUser(userId, userName) {
      currentChatUserId = userId;
      
      document.getElementById('chatModalTitle').innerHTML = `<i class="fas fa-comments"></i> Chat with ${escapeHtml(userName)}`;
      document.getElementById('chatModal').classList.add('active');
      document.body.style.overflow = 'hidden';
      
      await loadChatMessagesForUser(userId);
      
      const chatRef = window.dbRef(window.db, `chats/${userId}/messages`);
      window.dbOnValue(chatRef, () => {
        loadChatMessagesForUser(userId);
      });
    }

    async function loadChatMessagesForUser(userId) {
      try {
        const snapshot = await window.dbGet(window.dbRef(window.db, `chats/${userId}/messages`));
        const container = document.getElementById('chatMessagesContainer');
        container.innerHTML = '';

        if (snapshot.exists()) {
          const messages = snapshot.val();
          currentChatMessages = Object.entries(messages).map(([id, msg]) => ({
            id,
            ...msg
          })).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

          currentChatMessages.forEach(msg => {
            const messageDiv = createChatMessageElement(msg);
            container.appendChild(messageDiv);
          });

          container.scrollTop = container.scrollHeight;
        } else {
          container.innerHTML = `
            <div class="chat-empty-state">
              <div class="chat-empty-icon">💬</div>
              <div>No messages yet</div>
            </div>
          `;
        }
      } catch (error) {
        console.error('Error loading chat messages:', error);
      }
    }

    function createChatMessageElement(msg) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `chat-message ${msg.sender === 'admin' ? 'admin' : 'user'}`;
      messageDiv.dataset.messageId = msg.id;
      
      const time = new Date(msg.timestamp).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
      });

      const initial = msg.sender === 'admin' ? 'A' : 'U';

      messageDiv.innerHTML = `
        <div class="chat-message-avatar">${initial}</div>
        <div class="chat-message-content-wrapper">
          <div class="chat-message-content">
            ${escapeHtml(msg.message)}
          </div>
          <div class="chat-message-time">${time}</div>
        </div>
      `;

      if (msg.sender === 'admin') {
        const contentDiv = messageDiv.querySelector('.chat-message-content');
        
        contentDiv.addEventListener('mousedown', (e) => {
          longPressTimer = setTimeout(() => {
            showMessageActions(msg.id, contentDiv);
          }, 500);
        });

        contentDiv.addEventListener('mouseup', () => {
          clearTimeout(longPressTimer);
        });

        contentDiv.addEventListener('mouseleave', () => {
          clearTimeout(longPressTimer);
        });

        contentDiv.addEventListener('touchstart', (e) => {
          longPressTimer = setTimeout(() => {
            showMessageActions(msg.id, contentDiv);
          }, 500);
        });

        contentDiv.addEventListener('touchend', () => {
          clearTimeout(longPressTimer);
        });

        contentDiv.addEventListener('touchcancel', () => {
          clearTimeout(longPressTimer);
        });
      }

      return messageDiv;
    }

    function showMessageActions(messageId, contentElement) {
      document.querySelectorAll('.chat-message-actions').forEach(el => el.remove());

      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'chat-message-actions show';
      actionsDiv.innerHTML = `
        <button class="chat-message-action-btn" onclick="editMessage('${messageId}')">
          <i class="fas fa-edit"></i> Edit
        </button>
        <button class="chat-message-action-btn delete" onclick="deleteMessage('${messageId}')">
          <i class="fas fa-trash"></i> Delete
        </button>
      `;

      const messageDiv = contentElement.closest('.chat-message');
      messageDiv.style.position = 'relative';
      messageDiv.appendChild(actionsDiv);

      setTimeout(() => {
        document.addEventListener('click', function hideActions(e) {
          if (!actionsDiv.contains(e.target)) {
            actionsDiv.remove();
            document.removeEventListener('click', hideActions);
          }
        });
      }, 100);
    }

    async function editMessage(messageId) {
      const message = currentChatMessages.find(m => m.id === messageId);
      if (!message) return;

      document.getElementById('editMessageInput').value = message.message;
      currentEditMessageId = messageId;
      document.getElementById('editMessageModal').classList.add('active');
      document.body.style.overflow = 'hidden';

      document.querySelectorAll('.chat-message-actions').forEach(el => el.remove());
    }

    async function deleteMessage(messageId) {
      if (confirm('⚠️ Are you sure you want to delete this message?')) {
        try {
          await window.dbRemove(window.dbRef(window.db, `chats/${currentChatUserId}/messages/${messageId}`));
          window.showNotification('🗑️ Message deleted!');
          loadChatMessagesForUser(currentChatUserId);
        } catch (error) {
          alert('Error deleting message: ' + error.message);
        }
      }

      document.querySelectorAll('.chat-message-actions').forEach(el => el.remove());
    }

    async function saveEditedMessage() {
      const newText = document.getElementById('editMessageInput').value.trim();

      if (!newText) {
        alert('Message cannot be empty');
        return;
      }

      try {
        await window.dbUpdate(window.dbRef(window.db, `chats/${currentChatUserId}/messages/${currentEditMessageId}`), {
          message: newText,
          edited: true,
          editedAt: new Date().toISOString()
        });

        closeEditMessageModal();
        window.showNotification('✅ Message updated!');
        loadChatMessagesForUser(currentChatUserId);
      } catch (error) {
        alert('Error updating message: ' + error.message);
      }
    }

    function closeEditMessageModal() {
      document.getElementById('editMessageModal').classList.remove('active');
      document.getElementById('editMessageInput').value = '';
      currentEditMessageId = null;
      document.body.style.overflow = '';
    }

    document.getElementById('saveEditBtn')?.addEventListener('click', saveEditedMessage);
    document.getElementById('cancelEditBtn')?.addEventListener('click', closeEditMessageModal);

    async function sendAdminMessage() {
      const input = document.getElementById('chatInput');
      const message = input.value.trim();

      if (!message) {
        window.showNotification('Please enter a message', 'error');
        return;
      }

      if (!currentChatUserId) return;

      try {
        const chatRef = window.dbRef(window.db, `chats/${currentChatUserId}/messages`);
        const newMessageRef = window.dbPush(chatRef);

        await window.dbSet(newMessageRef, {
          message: message,
          sender: 'admin',
          timestamp: new Date().toISOString()
        });

        await window.dbUpdate(window.dbRef(window.db, `chats/${currentChatUserId}/info`), {
          lastMessage: message,
          lastMessageTime: new Date().toISOString()
        });

        input.value = '';
        window.showNotification('Message sent', 'success');

      } catch (error) {
        console.error('Error sending message:', error);
        window.showNotification('Failed to send message', 'error');
      }
    }

    document.getElementById('chatSendBtn')?.addEventListener('click', sendAdminMessage);

    document.getElementById('chatInput')?.addEventListener('keypress', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendAdminMessage();
      }
    });

    function closeChatModal() {
      document.getElementById('chatModal').classList.remove('active');
      document.body.style.overflow = '';
      currentChatUserId = null;
      currentChatMessages = [];
    }

    document.getElementById('chatModalClose')?.addEventListener('click', closeChatModal);

    window.openChatWithUser = openChatWithUser;
    window.editMessage = editMessage;
    window.deleteMessage = deleteMessage;

    async function saveSettings() {
      const displayName = document.getElementById('settingsDisplayName').value.trim();
      
      if (displayName && window.auth.currentUser) {
        try {
          await window.updateProfile(window.auth.currentUser, {
            displayName: displayName
          });
          document.getElementById('drawerUserName').textContent = displayName;
        } catch (error) {
          console.error('Error updating display name:', error);
        }
      }
      
      showMessage('settingsSuccess', '✅ Settings saved successfully!', 'success');
    }

    document.getElementById('saveSettingsBtn')?.addEventListener('click', saveSettings);

    document.getElementById('clearAllOrdersBtn')?.addEventListener('click', async function() {
      if (confirm('⚠️ WARNING: This will delete ALL orders permanently. This action cannot be undone!\n\nAre you absolutely sure?')) {
        if (confirm('🚨 FINAL WARNING: All order data will be lost forever. Continue?')) {
          try {
            window.showLoadingOverlay('Clearing all orders...');
            await window.dbRemove(window.dbRef(window.db, 'orders'));
            showMessage('settingsSuccess', '✅ All orders cleared successfully!', 'success');
            loadOrders();
            updateStats();
            window.hideLoadingOverlay();
            window.showNotification('✅ All orders cleared!');
          } catch (error) {
            window.hideLoadingOverlay();
            alert('Error clearing orders: ' + error.message);
          }
        }
      }
    });

    document.getElementById('clearAllDataBtn')?.addEventListener('click', async function() {
      if (confirm('🚨 EXTREME WARNING: This will delete ALL data (products, orders, coupons, settings) permanently!\n\nThis action CANNOT be undone!\n\nAre you absolutely sure?')) {
        if (confirm('⚠️ FINAL CONFIRMATION: Type "DELETE" in your mind and click OK to proceed.\n\nAll your data will be lost forever!')) {
          if (confirm('🔴 LAST CHANCE: Click OK to permanently delete everything, or Cancel to go back.')) {
            try {
              window.showLoadingOverlay('Clearing all data...');
              
              await window.dbRemove(window.dbRef(window.db, 'products'));
              await window.dbRemove(window.dbRef(window.db, 'orders'));
              await window.dbRemove(window.dbRef(window.db, 'coupons'));
              await window.dbRemove(window.dbRef(window.db, 'meta/brand'));
              await window.dbRemove(window.dbRef(window.db, 'meta/contact'));
              
              showMessage('settingsSuccess', '✅ All data cleared successfully! Refreshing...', 'success');
              
              setTimeout(() => {
                location.reload();
              }, 2000);
            } catch (error) {
              window.hideLoadingOverlay();
              alert('Error clearing data: ' + error.message);
            }
          }
        }
      }
    });

    document.querySelectorAll('.quick-action-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        const action = this.dataset.action;
        
        if (action === 'addProduct') {
          clearProductForm();
          switchTabFromDrawer('products');
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else if (action === 'createCoupon') {
          clearCouponForm();
          switchTabFromDrawer('coupons');
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else if (action === 'viewOrders') {
          switchTabFromDrawer('orders');
        } else if (action === 'viewUsers') {
          switchTabFromDrawer('users');
        }
      });
    });

    document.getElementById('fab')?.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    window.addEventListener('scroll', function() {
      const fab = document.getElementById('fab');
      if (window.scrollY > 300) {
        fab.style.display = 'flex';
      } else {
        fab.style.display = 'none';
      }
    });

    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab) {
          const searchInput = activeTab.querySelector('input[type="text"]');
          if (searchInput) {
            searchInput.focus();
          }
        }
      }
      
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab) {
          const saveBtn = activeTab.querySelector('.btn');
          if (saveBtn && !saveBtn.disabled) {
            saveBtn.click();
          }
        }
      }
    });

    window.addEventListener('beforeunload', (e) => {
      const isEditing = document.getElementById('editProductId').value || 
                       document.getElementById('editCouponId').value;
      
      if (isEditing) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    });

    window.addEventListener('error', (e) => {
      console.error('Global error:', e.error);
    });

    window.addEventListener('online', () => {
      console.log('🟢 Connection restored');
      window.showNotification('🟢 Connection restored');
    });

    window.addEventListener('offline', () => {
      console.log('🔴 Connection lost');
      window.showNotification('🔴 You are offline. Some features may not work.');
    });

    window.addEventListener('load', () => {
      if (window.performance) {
        const perfData = window.performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        console.log(`⚡ Page loaded in ${pageLoadTime}ms`);
      }
      
      updateDiscountInput();
      renderScreenshotUrls();
    });

    setTimeout(() => {
      if (window.auth.currentUser) {
        console.log(`%c🎉 Welcome to Admin Panel v3.0.0 Premium! 🎉`, 'color: #00ffff; font-size: 20px; font-weight: bold;');
        console.log(`%cLogged in as: ${window.auth.currentUser.email}`, 'color: #a855f7; font-size: 14px;');
        console.log(`%c💡 Tip: Use Ctrl+K to quickly search in any section`, 'color: #00ff88; font-size: 12px;');
        console.log(`%c🚀 New Features: Product Screenshots, User Support Chat, Password Display`, 'color: #ffa500; font-size: 12px;');
      }
    }, 2000);

    console.log('%c🔥 Admin Panel v3.0.0 Premium Loaded Successfully! 🔥', 'color: #00ffff; font-size: 16px; font-weight: bold; text-shadow: 0 0 10px #00ffff;');
    console.log('%c✨ New Features Added ✨', 'color: #a855f7; font-size: 14px; font-weight: bold;');
    console.log('%c• Product Screenshots Support', 'color: #00ff88; font-size: 12px;');
    console.log('%c• User Support Chat with Edit/Delete', 'color: #00ff88; font-size: 12px;');
    console.log('%c• Order Delete Functionality', 'color: #00ff88; font-size: 12px;');
    console.log('%c• Admin Password Display in Settings', 'color: #00ff88; font-size: 12px;');
    console.log('%c• Removed Email & Phone from Orders', 'color: #00ff88; font-size: 12px;');
    console.log('%c• Removed Export Orders Button', 'color: #00ff88; font-size: 12px;');
    console.log('%c• Drawer Hidden on Login/Setup Screen', 'color: #00ff88; font-size: 12px;');
  </script>
</body>
</html>""".encode("utf-8")

PAGES = {
    "/": USER_HTML,
    "/index.html": USER_HTML,
    "/user": USER_HTML,
    "/user/": USER_HTML,
    "/user.html": USER_HTML,
    "/admin": ADMIN_HTML,
    "/admin/": ADMIN_HTML,
    "/admin.html": ADMIN_HTML,
}


class AriyanHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._serve(send_body=True)

    def do_HEAD(self):
        self._serve(send_body=False)

    def _serve(self, send_body):
        path = urlsplit(self.path).path
        body = PAGES.get(path)
        content_type = "text/html; charset=utf-8"
        if path == "/healthz":
            body = b'{"status":"ok"}'
            content_type = "application/json; charset=utf-8"
        status = 200
        if body is None:
            status = 404
            body = b"<!doctype html><title>404</title><h1>Page not found</h1>"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if send_body:
            self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Run the bundled Ariyan website")
    parser.add_argument("--host", default=os.environ.get("ARIYAN_HOST") or "0.0.0.0")
    parser.add_argument("--port", type=int, default=os.environ.get("PORT") or "8000")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        server = ThreadingHTTPServer((args.host, args.port), AriyanHandler)
    except OSError as exc:
        parser.exit(1, f"Could not start server: {exc}\n")
    print(f"Listening on {args.host}:{server.server_port}", flush=True)
    display_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    print(f"User panel:  http://{display_host}:{args.port}/", flush=True)
    print(f"Admin panel: http://{display_host}:{args.port}/admin", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
