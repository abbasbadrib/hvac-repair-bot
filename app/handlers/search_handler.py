"""
Search handlers for customers and projects.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.customer_service import CustomerService
from app.services.project_service import ProjectService
import logging

logger = logging.getLogger(__name__)

# Conversation states
(SEARCH_QUERY, SEARCH_TYPE) = range(2)

class SearchHandler(BaseHandler):
    """Handler for search operations."""
    
    @staticmethod
    async def search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show search menu."""
        query = update.callback_query
        if query:
            await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("👤 جستجوی مشتری", callback_data="search_customer")],
            [InlineKeyboardButton("🛠 جستجوی پروژه", callback_data="search_project")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]
        ]
        
        await BaseHandler.send_message(
            update, context,
            "🔍 <b>جستجو</b>\n\n"
            "لطفاً نوع جستجو را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def search_customer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start customer search."""
        query = update.callback_query
        if query:
            await query.answer()
        
        context.user_data['search_type'] = 'customer'
        
        await BaseHandler.send_message(
            update, context,
            "🔍 <b>جستجوی مشتری</b>\n\n"
            "لطفاً عبارت جستجو را وارد کنید:\n"
            "(نام یا شماره تلفن)",
            parse_mode='HTML'
        )
        return SEARCH_QUERY
    
    @staticmethod
    async def search_project_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start project search."""
        query = update.callback_query
        if query:
            await query.answer()
        
        context.user_data['search_type'] = 'project'
        
        await BaseHandler.send_message(
            update, context,
            "🔍 <b>جستجوی پروژه</b>\n\n"
            "لطفاً عبارت جستجو را وارد کنید:\n"
            "(نام مشتری، شماره تلفن یا توضیحات پروژه)",
            parse_mode='HTML'
        )
        return SEARCH_QUERY
    
    @staticmethod
    async def search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute search."""
        query_text = update.message.text.strip()
        
        if len(query_text) < 2:
            await BaseHandler.send_message(
                update, context,
                "❌ عبارت جستجو باید حداقل ۲ کاراکتر باشد.",
                parse_mode='HTML'
            )
            return SEARCH_QUERY
        
        db = BaseHandler.get_db()
        try:
            search_type = context.user_data.get('search_type', 'customer')
            
            if search_type == 'customer':
                results = CustomerService.search(db, query_text)
                
                if not results:
                    await BaseHandler.send_message(
                        update, context,
                        f"🔍 <b>جستجوی مشتری</b>\n\n"
                        f"❌ هیچ مشتری با عبارت '{query_text}' یافت نشد.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 جستجوی مجدد", callback_data="search_customer")],
                            [InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")]
                        ]),
                        parse_mode='HTML'
                    )
                    return
                
                text = f"🔍 <b>نتایج جستجوی مشتری</b>\n\n"
                text += f"'{query_text}' :تعداد {len(results)} نتیجه برای\n\n"
                
                keyboard = []
                for i, customer in enumerate(results[:20], 1):
                    text += f"{i}. {customer.name} - 📞 {customer.phone}\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"👤 {customer.name}",
                            callback_data=f"view_customer_{customer.id}"
                        )
                    ])
                
                if len(results) > 20:
                    text += f"\n... و {len(results) - 20} نتیجه دیگر"
                
                keyboard.append([InlineKeyboardButton("🔙 جستجوی مجدد", callback_data="search_customer")])
                keyboard.append([InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")])
                
                await BaseHandler.send_message(
                    update, context,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                
            else:  # project search
                results = ProjectService.search(db, query_text)
                
                if not results:
                    await BaseHandler.send_message(
                        update, context,
                        f"🔍 <b>جستجوی پروژه</b>\n\n"
                        f"❌ هیچ پروژه‌ای با عبارت '{query_text}' یافت نشد.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 جستجوی مجدد", callback_data="search_project")],
                            [InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")]
                        ]),
                        parse_mode='HTML'
                    )
                    return
                
                text = f"🔍 <b>نتایج جستجوی پروژه</b>\n\n"
                text += f"'{query_text}' :تعداد {len(results)} نتیجه برای\n\n"
                
                keyboard = []
                from app.models.project import ProjectStatus
                for i, project in enumerate(results[:20], 1):
                    status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅" if project.status == ProjectStatus.COMPLETED else "❌"
                    text += f"{i}. {project.customer.name} - {project.project_type.value} - {status_emoji}\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🛠 {project.customer.name} - {project.project_type.value}",
                            callback_data=f"view_project_{project.id}"
                        )
                    ])
                
                if len(results) > 20:
                    text += f"\n... و {len(results) - 20} نتیجه دیگر"
                
                keyboard.append([InlineKeyboardButton("🔙 جستجوی مجدد", callback_data="search_project")])
                keyboard.append([InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")])
                
                await BaseHandler.send_message(
                    update, context,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در جستجو: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel search."""
        await BaseHandler.send_message(
            update, context,
            "❌ جستجو لغو شد.",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
