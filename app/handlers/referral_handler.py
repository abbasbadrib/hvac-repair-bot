"""
Referral management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.referral_service import ReferralService
from app.services.project_service import ProjectService
from app.services.part_service import PartService
from app.services.expense_service import ExpenseService
from app.services.payment_service import PaymentService
from app.domain.services.calculator_service import CalculatorService
from app.models.project import ProjectStatus
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
        # Check if called from main menu or callback
        if update.callback_query:
            query = update.callback_query
            project_id = int(query.data.split('_')[1])
            context.user_data['referral_project_id'] = project_id
            await query.answer()
        else:
            # Called from main menu - show list of projects
            db = BaseHandler.get_db()
            try:
                projects = ProjectService.get_all(db)
                if not projects:
                    await BaseHandler.send_message(
                        update, context,
                        "🤝 <b>حق معرفی</b>\n\n❌ هیچ پروژه‌ای ثبت نشده است.\n\n"
                        "لطفاً ابتدا یک پروژه ثبت کنید.",
                        reply_markup=get_main_keyboard(),
                        parse_mode='HTML'
                    )
                    return
                
                text = "🤝 <b>انتخاب پروژه برای ثبت حق معرفی</b>\n\n"
                keyboard = []
                for project in projects[:10]:
                    status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{status_emoji} {project.customer.name} - {project.project_type.value}",
                            callback_data=f"referral_{project.id}"
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
            project_id = context.user_data['referral_project_id']
            referral = ReferralService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not project:
                await BaseHandler.send_message(update, context, "❌ پروژه یافت نشد")
                return
            
            # Get financial data for calculations
            parts = PartService.get_by_project(db, project_id)
            expenses = ExpenseService.get_by_project(db, project_id)
            payments = PaymentService.get_by_project(db, project_id)
            total_payments = sum(p.amount for p in payments)
            
            # Calculate financials
            financials = CalculatorService.calculate_project_financials(
                total_amount_from_customer=project.labor_cost,
                parts=parts,
                expenses=expenses,
                referral_percentage=referral.percentage if referral else 0,
                referral_name=referral.referrer_name if referral else "",
                total_payments=total_payments
            )
            
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
                    f"👤 مشتری: {project.customer.name}\n"
                    f"💰 مبلغ کل پروژه: {project.labor_cost:,.0f} تومان\n\n"
                    "لطفاً معرفی‌کننده را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return
            
            # Show referral details with amounts
            text = (
                f"🤝 <b>اطلاعات حق معرفی</b>\n\n"
                f"👤 مشتری: {project.customer.name}\n"
                f"👤 معرفی کننده: {referral.referrer_name}\n"
                f"📊 درصد: {referral.percentage}%\n"
                f"💰 سود خالص پروژه: {financials.net_profit:,.0f} تومان\n"
                f"💵 مبلغ حق معرفی: {referral.amount:,.0f} تومان\n"
                f"💰 سود پس از کسر حق معرفی: {financials.net_profit - referral.amount:,.0f} تومان\n\n"
                f"📊 <b>تقسیم سود</b>:\n"
                f"👤 سهم من: {financials.my_share:,.0f} تومان\n"
                f"👥 سهم شریک: {financials.partner_share:,.0f} تومان\n"
                f"🤝 مبلغ قابل پرداخت به معرفی‌کننده: {referral.amount:,.0f} تومان"
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
            
            # Get financial data
            project = ProjectService.get_by_id(db, project_id)
            parts = PartService.get_by_project(db, project_id)
            expenses = ExpenseService.get_by_project(db, project_id)
            payments = PaymentService.get_by_project(db, project_id)
            total_payments = sum(p.amount for p in payments)
            
            financials = CalculatorService.calculate_project_financials(
                total_amount_from_customer=project.labor_cost,
                parts=parts,
                expenses=expenses,
                referral_percentage=percentage,
                referral_name=name,
                total_payments=total_payments
            )
            
            text = (
                f"✅ <b>حق معرفی با موفقیت ثبت شد!</b>\n\n"
                f"👤 معرفی کننده: {referral.referrer_name}\n"
                f"📊 درصد: {referral.percentage}%\n"
                f"💰 سود خالص: {financials.net_profit:,.0f} تومان\n"
                f"💵 مبلغ حق معرفی: {financials.referral_amount:,.0f} تومان\n\n"
                f"📊 <b>تقسیم سود نهایی</b>:\n"
                f"👤 سهم من: {financials.my_share:,.0f} تومان\n"
                f"👥 سهم شریک: {financials.partner_share:,.0f} تومان\n\n"
                f"🤝 مبلغ قابل پرداخت به {name}: {financials.referral_amount:,.0f} تومان"
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
            
            # Get financial data
            project = ProjectService.get_by_id(db, project_id)
            parts = PartService.get_by_project(db, project_id)
            expenses = ExpenseService.get_by_project(db, project_id)
            payments = PaymentService.get_by_project(db, project_id)
            total_payments = sum(p.amount for p in payments)
            
            financials = CalculatorService.calculate_project_financials(
                total_amount_from_customer=project.labor_cost,
                parts=parts,
                expenses=expenses,
                referral_percentage=percentage,
                referral_name=name,
                total_payments=total_payments
            )
            
            text = (
                f"✅ <b>حق معرفی با موفقیت ثبت شد!</b>\n\n"
                f"👤 معرفی کننده: {referral.referrer_name}\n"
                f"📊 درصد: {referral.percentage}%\n"
                f"💰 سود خالص: {financials.net_profit:,.0f} تومان\n"
                f"💵 مبلغ حق معرفی: {financials.referral_amount:,.0f} تومان\n\n"
                f"📊 <b>تقسیم سود نهایی</b>:\n"
                f"👤 سهم من: {financials.my_share:,.0f} تومان\n"
                f"👥 سهم شریک: {financials.partner_share:,.0f} تومان\n\n"
                f"🤝 مبلغ قابل پرداخت به {name}: {financials.referral_amount:,.0f} تومان"
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
