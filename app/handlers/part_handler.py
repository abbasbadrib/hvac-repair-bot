"""
Part management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.part_service import PartService
from app.services.project_service import ProjectService
import logging

logger = logging.getLogger(__name__)

# Conversation states
(PART_NAME, PART_QUANTITY, PART_PURCHASE, PART_SELLING) = range(4)

class PartHandler(BaseHandler):
    """Handler for part operations."""
    
    @staticmethod
    async def show_parts(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show parts for a project."""
        query = update.callback_query
        project_id = int(query.data.split('_')[1])
        context.user_data['current_project_id'] = project_id
        
        db = BaseHandler.get_db()
        try:
            parts = PartService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not parts:
                await query.answer()
                await BaseHandler.edit_message(
                    update, context,
                    f"🔩 <b>قطعات پروژه</b>\n\n"
                    f"مشتری: {project.customer.name}\n"
                    f"❌ هیچ قطعه‌ای ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ ثبت قطعه جدید", callback_data=f"add_part_{project_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = f"🔩 <b>قطعات پروژه</b>\n\n"
            text += f"👤 مشتری: {project.customer.name}\n"
            text += f"🛠 پروژه: {project.project_type.value} - {project.service_type}\n\n"
            
            total_profit = 0
            for i, part in enumerate(parts, 1):
                text += (
                    f"{i}. {part.name}\n"
                    f"   تعداد: {part.quantity} | قیمت خرید: {part.purchase_price:,.0f} | "
                    f"قیمت فروش: {part.selling_price:,.0f}\n"
                    f"   سود: {part.profit:,.0f} تومان\n\n"
                )
                total_profit += part.profit
            
            text += f"💰 <b>سود کل قطعات</b>: {total_profit:,.0f} تومان"
            
            keyboard = []
            for part in parts[:10]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"✏️ {part.name}",
                        callback_data=f"edit_part_{part.id}"
                    ),
                    InlineKeyboardButton(
                        "🗑",
                        callback_data=f"delete_part_{part.id}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("➕ ثبت قطعه جدید", callback_data=f"add_part_{project_id}")])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")])
            
            await query.answer()
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
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
            "🔩 <b>ثبت قطعه جدید</b>\n\n"
            "لطفاً <b>نام قطعه</b> را وارد کنید:",
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
        
        # Save part
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
                "✅ <b>قطعه با موفقیت ثبت شد!</b>\n\n"
                f"🔩 نام: {part.name}\n"
                f"🔢 تعداد: {part.quantity}\n"
                f"💰 قیمت خرید: {part.purchase_price:,.0f} تومان\n"
                f"💰 قیمت فروش: {part.selling_price:,.0f} تومان\n"
                f"📈 سود: {part.profit:,.0f} تومان"
            )
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت قطعه دیگر", callback_data=f"add_part_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به قطعات", callback_data=f"parts_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ]),
                parse_mode='HTML'
            )
            
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
    async def delete_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a part."""
        query = update.callback_query
        part_id = int(query.data.split('_')[2])
        
        db = BaseHandler.get_db()
        try:
            part = PartService.get_by_id(db, part_id)
            if not part:
                await query.answer("❌ قطعه یافت نشد", True)
                return
            
            project_id = part.project_id
            
            if PartService.delete(db, part_id):
                await query.answer("✅ قطعه حذف شد")
                await PartHandler.show_parts(update, context)
                logger.info(f"Part {part_id} deleted")
            else:
                await query.answer("❌ خطا در حذف قطعه", True)
        finally:
            db.close()
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد."
        )
        context.user_data.clear()
        return ConversationHandler.END
