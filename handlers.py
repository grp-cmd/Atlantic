"""Bot message handlers"""
from config import *
from utils import PortCalculator, FreightCalculator

def register_handlers(bot, engine):
    """Register all bot handlers"""
    
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        text = """🌊 *Atlantis AI Agent*

Advanced maritime logistics with:
• Freight cost calculator
• PDF quote generation  
• Document analysis
• Port database
• AI consultations

*Commands:*
/quote - Interactive quote + PDF
/analyze - Document analyzer
/ports - Port list
/carriers - Shipping companies
/docs - Documents guide
/status - System status

📄 Send document photos for analysis!
💡 Ask any shipping question!"""
        bot.reply_to(message, text, parse_mode='Markdown')
    
    @bot.message_handler(commands=['analyze'])
    def analyze_cmd(message):
        text = """📄 *Document Analyzer*

Send photos of:
• Bill of Lading
• Commercial Invoice
• Packing List
• Certificate of Origin
• Any shipping document

Add caption: "analyze this" or just send it!

I'll verify and provide detailed feedback."""
        bot.reply_to(message, text, parse_mode='Markdown')
    
    @bot.message_handler(commands=['docs'])
    def docs_guide(message):
        text = """📋 *Shipping Documents*

*EXPORT:*
• Commercial Invoice
• Packing List
• Bill of Lading
• Certificate of Origin

*IMPORT:*
• Customs Declaration
• Import License
• Delivery Order

*SPECIAL:*
• Insurance Certificate
• Dangerous Goods (if applicable)
• Health/Phyto Certificates

Send photo with /analyze for verification!"""
        bot.reply_to(message, text, parse_mode='Markdown')
    
    @bot.message_handler(commands=['ports'])
    def list_ports(message):
        text = "🌍 *Ports:*\n\n"
        for country, ports in PORTS_DATABASE.items():
            text += f"*{country.upper()}:*\n"
            for city, info in ports.items():
                text += f"  • {info['name']}\n"
            text += "\n"
        bot.reply_to(message, text, parse_mode='Markdown')
    
    @bot.message_handler(commands=['carriers'])
    def list_carriers(message):
        text = "🚢 *Carriers:*\n\n"
        for _, info in CARRIERS_DATABASE.items():
            text += f"*{info['name']}*\n{info['website']}\nRating: {info['rating']}/5\n\n"
        bot.reply_to(message, text, parse_mode='Markdown')
    
    @bot.message_handler(commands=['quote'])
    def start_quote(message):
        user_id = message.from_user.id
        user_sessions[user_id] = {"step": "origin_country"}
        bot.reply_to(message, "*Step 1/6:* Origin country?\n(e.g., Algeria, Spain, China)", parse_mode='Markdown')
    
    @bot.message_handler(commands=['status'])
    def status(message):
        pdf_status = "✅" if REPORTLAB_AVAILABLE else "❌"
        text = f"""✅ *Atlantis Status*

AI: Groq ({engine.model})
Ports: {len([p for ports in PORTS_DATABASE.values() for p in ports])}
PDF: {pdf_status}
Vision: ✅
System: 🟢 Online"""
        bot.reply_to(message, text, parse_mode='Markdown')
    
    @bot.message_handler(content_types=['photo'])
    def handle_photo(message):
        caption = (message.caption or "").lower()
        is_doc = any(w in caption for w in ["document", "invoice", "analyze", "check"])
        
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded = bot.download_file(file_info.file_path)
            vision_result = engine.analyze_vision(downloaded)
            
            if is_doc:
                bot.send_message(message.chat.id, f"👁️ Scan: {vision_result}\n\n⚙️ Analyzing...", parse_mode='Markdown')
                analysis = engine.analyze_shipping_document(vision_result)
                bot.send_message(message.chat.id, f"📋 *ANALYSIS*\n\n{analysis}", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"📸 Result: {vision_result}\n\n💡 Add 'analyze' caption for documents", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")
    
    @bot.message_handler(func=lambda m: True)
    def handle_text(message):
        user_id = message.from_user.id
        
        # Check if in quote wizard
        if user_id in user_sessions:
            handle_quote_steps(bot, engine, message, user_sessions)
            return
        
        # Regular AI response
        bot.send_chat_action(message.chat.id, 'typing')
        response = engine.get_logic(message.text)
        bot.reply_to(message, response)
        
        # Suggest /quote for cost questions
        if any(w in message.text.lower() for w in ["cost", "price", "calculate", "quote"]):
            bot.send_message(message.chat.id, "💡 Tip: Use /quote for detailed PDF quote!", parse_mode='Markdown')

def handle_quote_steps(bot, engine, message, sessions):
    """Handle multi-step quote wizard"""
    user_id = message.from_user.id
    session = sessions[user_id]
    text = message.text.strip().lower()
    
    if session["step"] == "origin_country":
        session["origin_country"] = text
        session["step"] = "origin_city"
        cities = ", ".join(PORTS_DATABASE.get(text, {}).keys()) or "any city"
        bot.reply_to(message, f"*Step 2/6:* Origin city/port?\n({cities})", parse_mode='Markdown')
    
    elif session["step"] == "origin_city":
        session["origin_city"] = text.replace(" ", "")
        session["step"] = "dest_country"
        bot.reply_to(message, "*Step 3/6:* Destination country?", parse_mode='Markdown')
    
    elif session["step"] == "dest_country":
        session["dest_country"] = text
        session["step"] = "dest_city"
        cities = ", ".join(PORTS_DATABASE.get(text, {}).keys()) or "any city"
        bot.reply_to(message, f"*Step 4/6:* Destination city?\n({cities})", parse_mode='Markdown')
    
    elif session["step"] == "dest_city":
        session["dest_city"] = text.replace(" ", "")
        session["step"] = "cargo"
        bot.reply_to(message, f"*Step 5/6:* Cargo type?\n({', '.join(CARGO_TYPES.keys())})", parse_mode='Markdown')
    
    elif session["step"] == "cargo":
        session["cargo"] = text
        session["step"] = "weight"
        bot.reply_to(message, "*Step 6/6:* Weight in tons?\n(e.g., 50)", parse_mode='Markdown')
    
    elif session["step"] == "weight":
        try:
            session["weight"] = float(text)
            generate_quote(bot, engine, message, session)
            del sessions[user_id]
        except:
            bot.reply_to(message, "❌ Invalid number. Try again:")

def generate_quote(bot, engine, message, session):
    """Generate and send quote"""
    bot.send_message(message.chat.id, "⚙️ Generating quote...")
    
    # Get ports
    origin_port = PortCalculator.find_port(session["origin_country"], session["origin_city"])
    dest_port = PortCalculator.find_port(session["dest_country"], session["dest_city"])
    
    if origin_port and dest_port:
        distance = PortCalculator.calculate_distance(
            origin_port["lat"], origin_port["lon"],
            dest_port["lat"], dest_port["lon"]
        )
        transit = PortCalculator.estimate_transit_time(distance)
        origin_name = origin_port["name"]
        dest_name = dest_port["name"]
    else:
        distance, transit = 1000, 10
        origin_name = f"{session['origin_city'].title()}, {session['origin_country'].title()}"
        dest_name = f"{session['dest_city'].title()}, {session['dest_country'].title()}"
    
    # Calculate costs
    cargo_info = CARGO_TYPES.get(session["cargo"], CARGO_TYPES["general"])
    costs = FreightCalculator.calculate_cost(distance, session["weight"], session["cargo"])
    
    # Send summary
    summary = f"""📦 *QUOTE SUMMARY*

*Route:* {origin_name} → {dest_name}
Distance: {distance:.0f} nm | Transit: ~{transit} days

*Cargo:* {session['cargo'].title()} | {session['weight']} tons
Container: {cargo_info['container']}

*Costs:*
Base: ${costs['base_freight']:,.0f}
Fuel: ${costs['bunker_surcharge']:,.0f}
Terminal: ${costs['terminal_handling']:,.0f}
Docs: ${costs['documentation']:,.0f}
Customs: ${costs['customs_broker']:,.0f}
Insurance: ${costs['insurance']:,.0f}

*TOTAL: ${costs['total']:,.0f} USD*

⚠️ Estimates only. Request formal quotes.
"""
    bot.send_message(message.chat.id, summary, parse_mode='Markdown')
    
    # AI insights
    context = f"Route: {origin_name} to {dest_name}, {session['weight']}t {session['cargo']}"
    insights = engine.get_logic("Give 3 key tips for this shipment", context)
    bot.send_message(message.chat.id, f"💡 *Tips:*\n{insights}", parse_mode='Markdown')
