"""
Referral management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.referral_service import ReferralService
from app.services.project_service import ProjectService
from app.keyboards.main_keyboard import get_main_keyboard
import logging
import json
import os

logger = logging.getLogger(__name__)

# Conversation states
REFERRAL_NAME, REFERRAL_PERCENTAGE = range(2)

# File to store referrers
REFERRERS_FILE = "referrers.json"

class ReferralHandler(BaseHandler):
    """Handler for referral operations."""
    
    REFERRAL_NAME = REFERRAL_NAME
    REFERRAL_PERCENTAGE = REFERRAL_PERCENTAGE
    
    @staticmethod
    def load_referrers():
        """Load referrers from file."""
        try:
            if os.path.exists(REFERRERS_FILE):
                with open(REFERRERS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    @staticmethod
    def save_referrers(referrers):
        """Save referrers to file."""
        try:
            with open(REFERRERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(referrers, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    @staticmethod
    async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show referral for a project."""
        query = update.callback_query
        if query:
            project_id = int(query.data.split('_')[1])
            context.user_data['referral_project_id'] = project_id
            await query.answer()
        else:
            await BaseHandler.send_message(
                update, context,
                "🤝 لطفاً ابتدا یک پروژه را انتخاب کنید.",
                reply_markup=get_main_keyboard()
            )
            return
        
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['referral_project_id']
            referral = ReferralService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not project:
                await BaseHandler.send_message(update, context, "❌ پروژه یافت نشد")
                return
            
            if not referral:
                # Show quick referral buttons
                referrers = ReferralHandler.load_referrers()
                keyboard = []
                
                # Add quick buttons for existing referrers
                for name, pct in referrers.items():
                    keyboard.append([
                        InlineKeyboardButton(
                            f"👤 {name} ({pct}%)", 
                            callback_data=f"ref_quick_{name}_{pct}"
                        )
                    ])
                
                keyboard.append([InlineKeyboardButton("➕ معرفی جدید", callback_data=f"add_referral_{project_id}")])
                keyboard.append([InlineKeyboardButton("⚙ مدیریت معرفی‌کننده‌ها", callback_data="manage_referrers")])
                keyboard.append([InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")])
                
                await BaseHandler.edit_message(
                    update, context,
                    f"🤝 <b>حق معرفی پروژه</b>\n\n"
                    f"👤 مشتری: {project.customer.name}\n\n"
                    "لطفاً معرفی‌کننده را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
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
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def quick_add_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick add referral from button."""
        query = update.callback_query
        data = query.data.split('_')
        # data: ref_quick_Name_25
        name = data[2]
        percentage = int(data[3])
        
        project_id = context.user_data.get('referral_project_id')
        if not project_id:
            await query.answer("❌ پروژه‌ای انتخاب نشده است", True)
            return
        
        context.user_data['referral_name'] = name
        context.user_data['referral_percentage'] = percentage
        context.user_data['referral_project_id'] = project_id
        
        await query.answer(f"✅ {name} با {percentage}% انتخاب شد")
        
        # Save referral
        db = BaseHandler.get_db()
        try:
            referral = ReferralService.create(
                db,
                project_id=project_id,
                referrer_name=name,
                percentage=percentage
            )
            
            text = (
                f"✅ <b>حق معرفی با موفقیت ثبت شد!</b>\n\n"
                f"👤 معرفی کننده: {referral.referrer_name}\n"
                f"📊 درصد: {referral.percentage}%\n"
                f"💰 مبلغ: {referral.amount:,.0f} تومان\n\n"
                "💡 مبلغ حق معرفی پس از تکمیل پروژه محاسبه می‌شود."
            )
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ]),
                parse_mode='HTML'
            )
            
            logger.info(f"Quick referral added: {name} - {percentage}% for project {project_id}")
            
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
        name = update.message.text.strip()
        context.user_data['referral_name'] = name
        
        # Check if we have this referrer
        referrers = ReferralHandler.load_referrers()
        
        if name in referrers:
            # Auto-set percentage
            context.user_data['referral_percentage'] = referrers[name]
            await ReferralHandler.save_referral(update, context, auto=True)
            return ConversationHandler.END
        
        # Ask for percentage
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("۰٪", callback_data="ref_pct_0"),
             InlineKeyboardButton("۱۰٪", callback_data="ref_pct_10"),
             InlineKeyboardButton("۱۵٪", callback_data="ref_pct_15")],
            [InlineKeyboardButton("۲۰٪", callback_data="ref_pct_20"),
             InlineKeyboardButton("۲۵٪", callback_data="ref_pct_25"),
             InlineKeyboardButton("✏️ دلخواه", callback_data="ref_pct_custom")],
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_referral")]
        ])
        
        await BaseHandler.send_message(
            update, context,
            f"📊 لطفاً <b>درصد حق معرفی</b> را انتخاب کنید:\n\n"
            f"👤 معرفی کننده: {name}",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return REFERRAL_PERCENTAGE
    
    @staticmethod
    async def add_referral_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get referral percentage from callback."""
        query = update.callback_query
        data = query.data
        await query.answer()
        
        if data == "cancel_referral":
            await ReferralHandler.cancel(update, context)
            return ConversationHandler.END
        
        if data == "ref_pct_custom":
            await BaseHandler.edit_message(
                update, context,
                "✏️ لطفاً <b>درصد</b> مورد نظر را وارد کنید (عدد بین 0 تا 100):",
                parse_mode='HTML'
            )
            return REFERRAL_PERCENTAGE
        
        percentage = int(data.split('_')[2])
        context.user_data['referral_percentage'] = percentage
        
        # Save referral
        await ReferralHandler.save_referral(update, context)
        return ConversationHandler.END
    
    @staticmethod
    async def add_referral_custom_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get custom percentage from text input."""
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
            return REFERRAL_PERCENTAGE
        
        await ReferralHandler.save_referral(update, context)
        return ConversationHandler.END
    
    @staticmethod
    async def save_referral(update: Update, context: ContextTypes.DEFAULT_TYPE, auto: bool = False):
        """Save referral to database."""
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['referral_project_id']
            name = context.user_data['referral_name']
            percentage = context.user_data['referral_percentage']
            
            referral = ReferralService.create(
                db,
                project_id=project_id,
                referrer_name=name,
                percentage=percentage
            )
            
            # Save to referrers list
            referrers = ReferralHandler.load_referrers()
            if name not in referrers:
                referrers[name] = percentage
                ReferralHandler.save_referrers(referrers)
            
            text = (
                f"✅ <b>حق معرفی با موفقیت ثبت شد!</b>\n\n"
                f"👤 معرفی کننده: {referral.referrer_name}\n"
                f"📊 درصد: {referral.percentage}%\n"
                f"💰 مبلغ: {referral.amount:,.0f} تومان\n\n"
                "💡 مبلغ حق معرفی پس از تکمیل پروژه محاسبه می‌شود."
            )
            
            if auto:
                text += f"\n🔹 درصد {percentage}% به‌طور خودکار برای '{name}' تنظیم شد."
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ]),
                parse_mode='HTML'
            )
            
            logger.info(f"New referral added for project {project_id}: {name} - {percentage}%")
            
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
    async def manage_referrers(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage referrers list."""
        query = update.callback_query
        await query.answer()
        
        referrers = ReferralHandler.load_referrers()
        
        if not referrers:
            text = "📋 <b>لیست معرفی‌کننده‌ها</b>\n\n❌ هیچ معرفی‌کننده‌ای ثبت نشده است."
        else:
            text = "📋 <b>لیست معرفی‌کننده‌ها</b>\n\n"
            for name, pct in referrers.items():
                text += f"👤 {name}: {pct}%\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ افزودن معرفی‌کننده جدید", callback_data="add_referrer")],
            [InlineKeyboardButton("🗑 حذف معرفی‌کننده", callback_data="remove_referrer")],
            [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data="back_to_referral")]
        ]
        
        await BaseHandler.edit_message(
            update, context,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def add_referrer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new referrer."""
        query = update.callback_query
        await query.answer()
        
        await BaseHandler.edit_message(
            update, context,
            "➕ <b>افزودن معرفی‌کننده جدید</b>\n\n"
            "لطفاً <b>نام</b> معرفی‌کننده را وارد کنید:",
            parse_mode='HTML'
        )
        return REFERRAL_NAME
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد.",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
