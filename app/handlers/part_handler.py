# فقط بخش نمایش قطعات را اصلاح می‌کنیم:

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
