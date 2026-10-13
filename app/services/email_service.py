import logging
from html import escape
from email.message import EmailMessage
from typing import Optional

import aiosmtplib
from pydantic import EmailStr

from app.core.config import (
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_TLS,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


async def send_email(
    to_email: EmailStr,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD:
        return False

    message = EmailMessage()
    message["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
    message["To"] = to_email
    message["Subject"] = subject

    if text_content:
        message.set_content(text_content)
        message.add_alternative(html_content, subtype="html")
    else:
        message.set_content(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=SMTP_TLS,
        )
        return True
    except Exception:
        logger.exception("Email delivery failed")
        return False


def render_welcome_email(name: str) -> tuple[str, str]:
    safe_name = escape(name)
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Welcome to Mini E-Commerce, {safe_name}!</h2>
                <p>Thank you for registering. Your account is now ready to use.</p>
                <p>You can now:</p>
                <ul>
                    <li>Browse and purchase products</li>
                    <li>Register product warranties</li>
                    <li>Track your orders</li>
                    <li>Manage your addresses</li>
                </ul>
                <p style="margin-top: 30px;">Happy shopping!</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #9ca3af;">If you didn't create this account, please ignore this email.</p>
            </div>
        </body>
    </html>
    """
    text = f"Welcome to Mini E-Commerce, {name}!\n\nThank you for registering. Your account is now ready to use."
    return html, text


def render_order_confirmation_email(
    name: str,
    order_id: int,
    total_amount: str,
    items: list[dict],
) -> tuple[str, str]:
    items_html = "".join(
        f"<tr><td>{escape(str(item['name']))}</td><td>{escape(str(item['quantity']))}</td><td>${escape(str(item['price']))}</td></tr>"
        for item in items
    )
    safe_name = escape(name)
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Order Confirmation - #{order_id}</h2>
                <p>Hi {safe_name},</p>
                <p>Thank you for your order! Your order has been confirmed.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #f3f4f6;">
                            <th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Product</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Qty</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                <p style="font-weight: bold; font-size: 18px;">Total: ${total_amount}</p>
                <p>We'll notify you when your order ships.</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #9ca3af;">Mini E-Commerce</p>
            </div>
        </body>
    </html>
    """
    text = f"Order Confirmation - #{order_id}\n\nHi {name},\n\nThank you for your order! Total: ${total_amount}"
    return html, text


def render_warranty_registration_email(
    name: str,
    product_name: str,
    serial_number: str,
    warranty_end_date: str,
    status: str,
) -> tuple[str, str]:
    safe_name = escape(name)
    safe_product_name = escape(product_name)
    safe_serial_number = escape(serial_number)
    safe_status = escape(status)
    safe_expiry = escape(warranty_end_date)
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Warranty Registered Successfully</h2>
                <p>Hi {safe_name},</p>
                <p>Your warranty for <strong>{safe_product_name}</strong> has been registered.</p>
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Serial Number:</strong> {safe_serial_number}</p>
                    <p><strong>Warranty Status:</strong> {safe_status}</p>
                    <p><strong>Warranty Expires:</strong> {safe_expiry}</p>
                </div>
                <p>You can check your warranty status anytime in your account.</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #9ca3af;">Mini E-Commerce</p>
            </div>
        </body>
    </html>
    """
    text = f"Warranty Registered\n\nHi {name},\n\nYour warranty for {product_name} (Serial: {serial_number}) has been registered. Status: {status}, Expires: {warranty_end_date}"
    return html, text


def render_payment_confirmation_email(
    name: str,
    order_id: int,
    amount: str,
    method: str,
    transaction_id: str,
) -> tuple[str, str]:
    safe_name = escape(name)
    safe_method = escape(method)
    safe_transaction_id = escape(transaction_id)
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Payment Confirmed</h2>
                <p>Hi {safe_name},</p>
                <p>Your payment for order <strong>#{order_id}</strong> has been processed successfully.</p>
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Amount:</strong> ${amount}</p>
                    <p><strong>Method:</strong> {safe_method}</p>
                    <p><strong>Transaction ID:</strong> {safe_transaction_id}</p>
                </div>
                <p>Your order is now confirmed and will be processed shortly.</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #9ca3af;">Mini E-Commerce</p>
            </div>
        </body>
    </html>
    """
    text = f"Payment Confirmed\n\nHi {name},\n\nYour payment for order #{order_id} of ${amount} via {method} has been processed. Transaction ID: {transaction_id}"
    return html, text