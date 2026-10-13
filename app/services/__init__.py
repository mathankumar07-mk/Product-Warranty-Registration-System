from app.services.address_service import *
from app.services.admin_service import *
from app.services.auth_service import *
from app.services.cart_service import *
from app.services.category_service import *
from app.services.email_service import *
from app.services.invoice_service import *
from app.services.notification_service import *
from app.services.order_service import *
from app.services.payment_service import *
from app.services.product_service import *
from app.services.user_service import *
from app.services.warranty_service import *

__all__ = [
    "send_email",
    "render_welcome_email",
    "render_order_confirmation_email",
    "render_warranty_registration_email",
    "render_payment_confirmation_email",
    "create_address",
    "get_address",
    "list_addresses",
    "update_address",
    "delete_address",
    "create_admin",
    "register_user",
    "authenticate_user",
    "create_admin",
    "get_or_create_cart",
    "get_cart",
    "add_to_cart",
    "update_cart_item",
    "remove_from_cart",
    "clear_cart",
    "create_category",
    "get_category",
    "update_category",
    "delete_category",
    "create_invoice",
    "get_invoice",
    "get_invoice_by_order",
    "update_invoice_file",
    "create_notification",
    "add_user_notification",
    "create_user_notification",
    "get_notification",
    "list_notifications",
    "mark_as_read",
    "mark_all_as_read",
    "create_order",
    "get_order",
    "list_orders",
    "update_order_status",
    "create_payment",
    "get_payment",
    "list_payments_for_order",
    "update_payment",
    "simulate_payment",
    "create_product",
    "get_product",
    "list_products",
    "update_product",
    "delete_product",
    "update_user",
    "create_warranty_policy",
    "get_warranty_policy",
    "get_warranty_policy_by_product",
    "update_warranty_policy",
    "register_warranty",
    "get_registration",
    "list_user_registrations",
    "update_registration_status",
    "check_warranty_validity",
]