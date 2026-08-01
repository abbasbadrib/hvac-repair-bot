"""
Referral management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.referral_service import ReferralService
from app.services.project_service import ProjectService
from app.keyboards.referral_keyboard import get_referral_percentage_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
(REFERRAL_NAME, REFERRAL_PERCENTAGE, REFERRAL_CUSTOM) = range(3)

class ReferralHandler(BaseHandler):
    """Handler for referral operations."""
    
    @staticmethod
    async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show referral for a project."""
        query = update.callback_query
        project_id = int(query.data.split('_')[1])
        context.user_data['referral_project_id'] = project_id
        
        db = BaseHandler.get_db()
        try:
            referral = ReferralService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not referral:
                await query.answer()
                await BaseHandler.edit_message(
                    update, context,
                    f"🤝 <b>حق معرفی پروژه</b>\n\n"
                    f"👤 مشتری: {project.customer.name}\n"
                    f"❌ هیچ حق معرفی ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ ثبت حق معرفی", callback_data=f"add_referral_{project_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = (
                f"🤝 <b>اطلاعات حق معرفی</b>\n\n"
                f"👤 مشتری: {project.customer.name}\n"
                f"👤 معرفی کننده: {referral.referrer_name}\n"
                f"📊 درصد: {referral.percentage}%\n"
                f"💰 مبلغ: {referral.amount:,.0f} تومان"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_referral_{referral.id}"),
                    InlineKeyboardButton("🗑 حذف", callback_data=f"delete_referral_{referral.id}")
                ],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ]
            
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
    async def add_referral_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new referral."""
        query = update.callback_query
        project_id = int(query.data.split('_')[2])
        context.user_data['referral_project_id'] = project_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "🤝 <b>ثبت حق معرفی</b>\n\n"
            "لطفاً <b>نام</b> معرفی کننده را وارد کنید:",
            parse_mode='HTML'
        )
        return REFERRAL_NAME
    
    @staticmethod
    async def add_referral_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get referrer name."""
        context.user_data['referral_name'] = update.message.text.strip()
        
        await BaseHandler.send_message(
            update, context,
            "📊 لطفاً <b>درصد حق معرفی</b> را انتخاب کنید:",
            reply_markup=get_referral_percentage_keyboard(context.user_data['referral_project_id']),
            parse_mode='HTML'
        )
        return REFERRAL_PERCENTAGE
    
    @staticmethod
    async def add_referral_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get referral percentage."""
        query = update.callback_query
        parts = query.data.split('_')
        
        if parts[1] == 'custom':
            # Custom percentage
            await query.answer()
            await BaseHandler.edit_message(
                update, context,
                "✏️ لطفاً <b>درصد</b> مورد نظر را وارد کنید (عدد بین 0 تا 100):",
                parse_mode='HTML'
            )
            return REFERRAL_CUSTOM
        
        percentage = int(parts[3])
        context.user_data['referral_percentage'] = percentage
        
        # Save referral
        await ReferralHandler.save_referral(update, context)
        return ConversationHandler.END
    
    @staticmethod
    async def add_referral_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get custom percentage."""
        try:
            percentage = float(update.message.text.strip())
            if percentage < 0 or percentage > 100:
                raise ValueError("Percentage must be between 0 and 100")
            context.user_data['referral_percentage'] = percentage
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ درصد نامعتبر است. لطفاً عددی بین 0 تا 100 وارد کنید.",
                parse_mode='HTML'
            )
            return REFERRAL_CUSTOM
        
        await ReferralHandler.save_referral(update, context)
        return ConversationHandler.END
    
    @staticmethod
    async def save_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save referral to database."""
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['referral_project_id']
            
            referral = ReferralService.create(
                db,
                project_id=project_id,
                referrer_name=context.user_data['referral_name'],
                percentage=context.user_data['referral_percentage']
            )
            
            text = (
                "✅ <b>حق معرفی با موفقیت ثبت شد!</b>\n\n"
                f"👤 معرفی کننده: {referral.referrer_name}\n"
                f"📊 درصد: {referral.percentage}%\n"
                f"💰 مبلغ: {referral.amount:,.0f} تومان\n\n"
                "💡 مبلغ حق معرفی پس از تکمیل پروژه محاسبه می‌شود."
            )
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ]),
                parse_mode='HTML'
            )
            
            logger.info(f"New referral added for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error adding referral: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت حق معرفی: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
    
    @staticmethod
    async def delete_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a referral."""
        query = update.callback_query
        referral_id = int(query.data.split('_')[2])
        
        db = BaseHandler.get_db()
        try:
            referral = ReferralService.get_by_id(db, referral_id)
            if not referral:
                await query.answer("❌ حق معرفی یافت نشد", True)
                return
            
            project_id = referral.project_id
            
            if ReferralService.delete(db, referral_id):
                await query.answer("✅ حق معرفی حذف شد")
                await BaseHandler.edit_message(
                    update, context,
                    "✅ حق معرفی با موفقیت حذف شد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                    ]),
                    parse_mode='HTML'
                )
                logger.info(f"Referral {referral_id} deleted")
            else:
                await query.answer("❌ خطا در حذف حق معرفی", True)
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
