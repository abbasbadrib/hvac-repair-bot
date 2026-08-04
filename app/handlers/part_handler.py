"""
Part management handlers with menu support.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.part_service import PartService
from app.services.project_service import ProjectService
from app.keyboards.main_keyboard import get_main_keyboard
from app.models.project import ProjectStatus
import logging

logger = logging.getLogger(__name__)

# Conversation states
PART_NAME, PART_QUANTITY, PART_PURCHASE, PART_SELLING = range(4)

class PartHandler(BaseHandler):
    """Handler for part operations."""
    
    PART_NAME = PART_NAME
    PART_QUANTITY = PART_QUANTITY
    PART_PURCHASE = PART_PURCHASE
    PART_SELLING = PART_SELLING
    
    @staticmethod
    async def show_parts(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show parts for a project."""
        # Check if called from main menu or callback
        if update.callback_query:
            query = update.callback_query
            data = query.data
            
            # اگر از منوی اصلی آمده باشد
            if data == "menu_parts":
                await query.answer()
                db = BaseHandler.get_db()
                try:
                    projects = ProjectService.get_all(db)
                    if not projects:
                        await BaseHandler.edit_message(
                            update, context,
                            "🔩 <b>قطعات</b>\n\n"
                            "❌ هیچ پروژه‌ای ثبت نشده است.\n\n"
                            "لطفاً ابتدا یک پروژه ثبت کنید.",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
                            ]),
                            parse_mode='HTML'
                        )
                        return
                    
                    text = "🔩 <b>انتخاب پروژه برای مدیریت قطعات</b>\n\n"
                    keyboard = []
                    for project in projects[:10]:
                        status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅"
                        keyboard.append([
                            InlineKeyboardButton(
                                f"{status_emoji} {project.customer.name} - {project.project_type.value}",
                                callback_data=f"parts_{project.id}"
                            )
                        ])
                    keyboard.append([InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")])
                    
                    await BaseHandler.edit_message(
                        update, context,
                        text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                    return
                finally:
                    db.close()
            
            # اگر از انتخاب پروژه آمده باشد
            if data.startswith("parts_"):
                try:
                    project_id = int(data.split('_')[1])
                    context.user_data['current_project_id'] = project_id
                    await query.answer()
                except (IndexError, ValueError) as e:
                    logger.error(f"Error parsing project_id: {e}")
                    await query.answer("❌ خطا در شناسایی پروژه", show_alert=True)
                    return
            else:
                await query.answer()
                return
        else:
            # از منوی اصلی (Reply Keyboard)
            db = BaseHandler.get_db()
            try:
                projects = ProjectService.get_all(db)
                if not projects:
                    await BaseHandler.send_message(
                        update, context,
                        "🔩 <b>قطعات</b>\n\n"
                        "❌ هیچ پروژه‌ای ثبت نشده است.\n\n"
                        "لطفاً ابتدا یک پروژه ثبت کنید.",
                        reply_markup=get_main_keyboard(),
                        parse_mode='HTML'
                    )
                    return
                
                text = "🔩 <b>انتخاب پروژه برای مدیریت قطعات</b>\n\n"
                keyboard = []
                for project in projects[:10]:
                    status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{status_emoji} {project.customer.name} - {project.project_type.value}",
                            callback_data=f"parts_{project.id}"
                        )
                    ])
                keyboard.append([InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")])
                
                await BaseHandler.send_message(
                    update, context,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return
            finally:
                db.close()
        
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data.get('current_project_id')
            if not project_id:
                await BaseHandler.send_message(update, context, "❌ پروژه‌ای انتخاب نشده است")
                return
            
            parts = PartService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not parts:
                text = f"🔩 <b>قطعات پروژه</b>\n\n👤 مشتری: {project.customer.name}\n❌ هیچ قطعه‌ای ثبت نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت قطعه جدید", callback_data=f"add_part_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ])
                await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
                return
            
            text = f"🔩 <b>قطعات پروژه</b>\n\n👤 مشتری: {project.customer.name}\n\n"
            total_profit = 0
            for i, part in enumerate(parts, 1):
                text += f"{i}. {part.name}\n"
                text += f"   تعداد: {part.quantity}\n"
                text += f"   💰 قیمت خرید: {part.purchase_price:,.0f} تومان\n"
                text += f"   💰 قیمت فروش: {part.selling_price:,.0f} تومان\n"
                text += f"   📈 سود: {part.profit:,.0f}\n\n"
                total_profit += part.profit
            
            text += f"💰 <b>سود کل قطعات</b>: {total_profit:,.0f} تومان"
            
            keyboard = [
                [InlineKeyboardButton("➕ ثبت قطعه جدید", callback_data=f"add_part_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ]
            
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def add_part_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new part."""
        query = update.callback_query
        project_id = int(query.data.split('_')[2])
        context.user_data['part_project_id'] = project_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "🔩 <b>ثبت قطعه جدید</b>\n\nلطفاً <b>نام قطعه</b> را وارد کنید:",
            parse_mode='HTML'
        )
        return PART_NAME
    
    @staticmethod
    async def add_part_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get part name."""
        context.user_data['part_name'] = update.message.text.strip()
        await BaseHandler.send_message(
            update, context,
            "🔢 تعداد قطعه را وارد کنید:",
            parse_mode='HTML'
        )
        return PART_QUANTITY
    
    @staticmethod
    async def add_part_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get part quantity."""
        try:
            quantity = int(update.message.text.strip())
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            context.user_data['part_quantity'] = quantity
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ تعداد نامعتبر است. لطفاً یک عدد مثبت وارد کنید.",
                parse_mode='HTML'
            )
            return PART_QUANTITY
        
        await BaseHandler.send_message(
            update, context,
            "💰 قیمت <b>خرید</b> هر قطعه را وارد کنید (تومان):",
            parse_mode='HTML'
        )
        return PART_PURCHASE
    
    @staticmethod
    async def add_part_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get purchase price."""
        try:
            price = float(update.message.text.replace(',', '').strip())
            if price < 0:
                raise ValueError("Price must be positive")
            context.user_data['part_purchase'] = price
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ قیمت نامعتبر است. لطفاً یک عدد وارد کنید.",
                parse_mode='HTML'
            )
            return PART_PURCHASE
        
        await BaseHandler.send_message(
            update, context,
            "💰 قیمت <b>فروش</b> هر قطعه را وارد کنید (تومان):",
            parse_mode='HTML'
        )
        return PART_SELLING
    
    @staticmethod
    async def add_part_selling(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get selling price and save part."""
        try:
            price = float(update.message.text.replace(',', '').strip())
            if price < 0:
                raise ValueError("Price must be positive")
            context.user_data['part_selling'] = price
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ قیمت نامعتبر است. لطفاً یک عدد وارد کنید.",
                parse_mode='HTML'
            )
            return PART_SELLING
        
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['part_project_id']
            part = PartService.create(
                db,
                project_id=project_id,
                name=context.user_data['part_name'],
                quantity=context.user_data['part_quantity'],
                purchase_price=context.user_data['part_purchase'],
                selling_price=context.user_data['part_selling']
            )
            
            text = (
                f"✅ <b>قطعه با موفقیت ثبت شد!</b>\n\n"
                f"🔩 نام: {part.name}\n"
                f"🔢 تعداد: {part.quantity}\n"
                f"💰 قیمت خرید: {part.purchase_price:,.0f} تومان\n"
                f"💰 قیمت فروش: {part.selling_price:,.0f} تومان\n"
                f"📈 سود: {part.profit:,.0f} تومان"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت قطعه دیگر", callback_data=f"add_part_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به قطعات", callback_data=f"parts_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ])
            
            await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
            logger.info(f"New part added: {part.name} for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error adding part: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت قطعه: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        context.user_data.clear()
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
