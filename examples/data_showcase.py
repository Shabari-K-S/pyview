"""E-Commerce Inventory & Live Order Management System."""

import pyview as pv
import pandas as pd

# 1. Product Catalog Data for Interactive Dataframe
PRODUCTS_DATA = [
    {"SKU": "PRD-001", "Product": "Wireless Noise-Canceling Headphones", "Category": "Audio", "Price": 199.99, "Stock Level": 85, "Capacity": 85, "In Stock": True, "Supplier": "https://supplier.audio.io"},
    {"SKU": "PRD-002", "Product": "Ultra-Wide Gaming Monitor 34\"", "Category": "Displays", "Price": 499.50, "Stock Level": 42, "Capacity": 42, "In Stock": True, "Supplier": "https://supplier.displays.net"},
    {"SKU": "PRD-003", "Product": "Mechanical Ergonomic Keyboard", "Category": "Peripherals", "Price": 129.00, "Stock Level": 18, "Capacity": 18, "In Stock": True, "Supplier": "https://supplier.peripherals.com"},
    {"SKU": "PRD-004", "Product": "USB-C Multi-Port Hub (10-in-1)", "Category": "Accessories", "Price": 59.95, "Stock Level": 95, "Capacity": 95, "In Stock": True, "Supplier": "https://supplier.hub.org"},
    {"SKU": "PRD-005", "Product": "Studio Broadcast Microphone", "Category": "Audio", "Price": 149.00, "Stock Level": 0, "Capacity": 0, "In Stock": False, "Supplier": "https://supplier.audio.io"},
    {"SKU": "PRD-006", "Product": "Precision Bluetooth Mouse", "Category": "Peripherals", "Price": 79.99, "Stock Level": 64, "Capacity": 64, "In Stock": True, "Supplier": "https://supplier.peripherals.com"},
    {"SKU": "PRD-007", "Product": "Aluminum Laptop Cooling Stand", "Category": "Accessories", "Price": 39.50, "Stock Level": 52, "Capacity": 52, "In Stock": True, "Supplier": "https://supplier.hub.org"},
    {"SKU": "PRD-008", "Product": "4K HDR Webcam with Stereo Mic", "Category": "Displays", "Price": 119.00, "Stock Level": 31, "Capacity": 31, "In Stock": True, "Supplier": "https://supplier.displays.net"},
]

# 2. Initial Order Batch Data
INITIAL_ORDERS = [
    {"Customer": "Acme Corp", "Product": "Wireless Noise-Canceling Headphones", "Quantity": 5, "Unit Price": 199.99, "Priority": "Express", "Paid": True},
    {"Customer": "Global Logistics", "Product": "Ultra-Wide Gaming Monitor 34\"", "Quantity": 2, "Unit Price": 499.50, "Priority": "Standard", "Paid": True},
    {"Customer": "Nexus Studios", "Product": "Mechanical Ergonomic Keyboard", "Quantity": 10, "Unit Price": 129.00, "Priority": "Express", "Paid": False},
    {"Customer": "Cyberdyne Systems", "Product": "USB-C Multi-Port Hub (10-in-1)", "Quantity": 8, "Unit Price": 59.95, "Priority": "Standard", "Paid": True},
]

# 3. Static Shipping Rates Matrix
SHIPPING_RATES = {
    "Destination Region": ["North America (Domestic)", "European Union", "Asia-Pacific", "Latin America", "Rest of World"],
    "Standard Delivery": ["$8.50 (3-5 days)", "$16.00 (5-8 days)", "$22.00 (6-10 days)", "$25.00 (7-12 days)", "$35.00 (10-15 days)"],
    "Express Air Cargo": ["$18.00 (1-2 days)", "$32.00 (2-3 days)", "$45.00 (3-4 days)", "$48.00 (3-5 days)", "$65.00 (4-6 days)"],
    "Free Shipping Threshold": ["Orders > $75", "Orders > $150", "Orders > $200", "Orders > $250", "Not Available"],
}

# Main Application Header
pv.title("📦 E-Commerce Inventory & Order Processing System")
pv.write("Manage product catalogs, edit customer orders in real time, and view international shipping logistics.")

# Tabbed Layout for Data Elements
tab_catalog, tab_editor, tab_rates, tab_telemetry = pv.tabs([
    "📊 Product Catalog",
    "✏️ Live Order Batch",
    "📑 Shipping Rates",
    "🔍 Telemetry & Logs",
])


# --- Tab 1: Interactive Dataframe ---
with tab_catalog:
    pv.header("Inventory Catalog & Stock Levels")
    pv.write("Search items, sort columns, and monitor stock fill levels.")
    
    df_products = pd.DataFrame(PRODUCTS_DATA)
    
    pv.dataframe(
        df_products,
        column_config={
            "Price": pv.column_config.NumberColumn("Price (USD)", format="$%.2f"),
            "Capacity": pv.column_config.ProgressColumn("Stock %", min_value=0, max_value=100),
            "Supplier": pv.column_config.LinkColumn("Supplier Portal", display_text="Visit Portal ↗"),
            "In Stock": pv.column_config.CheckboxColumn("Available"),
        },
    )

# --- Tab 2: Reactive Data Editor ---
with tab_editor:
    pv.header("Interactive Order Batch Processing")
    pv.write("Edit quantities, prices, or add new order rows below. Summary metrics recalculate automatically!")
    
    # Render reactive data editor widget
    edited_orders = pv.data_editor(
        INITIAL_ORDERS,
        num_rows="dynamic",
        key="orders_batch_editor",
        column_config={
            "Customer": pv.column_config.TextColumn("Customer Account", required=True),
            "Product": pv.column_config.SelectboxColumn("Item Ordered", options=[p["Product"] for p in PRODUCTS_DATA]),
            "Quantity": pv.column_config.NumberColumn("Qty", min_value=1, max_value=500, step=1, default=1),
            "Unit Price": pv.column_config.NumberColumn("Price ($)", min_value=0.0, format="$%.2f", default=50.0),
            "Priority": pv.column_config.SelectboxColumn("Fulfillment", options=["Standard", "Express", "Overnight"], default="Standard"),
            "Paid": pv.column_config.CheckboxColumn("Settled", default=False),
        },
    )
    
    # Calculate live totals from edited orders
    total_orders = len(edited_orders)
    gross_total = 0.0
    paid_count = 0
    
    for r in (edited_orders if isinstance(edited_orders, list) else edited_orders.to_dict(orient="records")):
        try:
            qty = float(r.get("Quantity") or 0)
            price = float(r.get("Unit Price") or 0)
            gross_total += qty * price
            if r.get("Paid"):
                paid_count += 1
        except (ValueError, TypeError):
            pass
            
    tax_total = gross_total * 0.08
    net_revenue = gross_total - tax_total
    
    # Real-Time Calculated Metrics Row
    m1, m2, m3, m4 = pv.columns([1, 1, 1, 1])
    with m1:
        pv.metric("Total Batch Orders", str(total_orders))
    with m2:
        pv.metric("Gross Revenue", f"${gross_total:,.2f}", delta=f"+${gross_total:,.2f}", delta_color="normal")
    with m3:
        pv.metric("Estimated Tax (8%)", f"${tax_total:,.2f}")
    with m4:
        settled_rate = f"{(paid_count / total_orders * 100):.0f}%" if total_orders > 0 else "0%"
        pv.metric("Settlement Rate", settled_rate, delta=f"{paid_count}/{total_orders} Paid", delta_color="normal")

# --- Tab 3: Static Table ---
with tab_rates:
    pv.header("Global Logistics & Shipping Schedule")
    pv.write("Standard and express freight rates across international hubs.")
    pv.table(SHIPPING_RATES)

# --- Tab 4: JSON Tree Viewer ---
with tab_telemetry:
    pv.header("Live Order Telemetry Payload")
    pv.write("Interactive JSON tree with collapsible nested objects and copy button.")
    
    telemetry_payload = {
        "batch_id": "BATCH-2026-0829-01",
        "warehouse": {
            "region": "US-East-1 (Virginia Hub)",
            "status": "Operational",
            "active_workers": 18,
            "connected_carriers": ["FedEx Logistics", "DHL Express", "UPS Freight"],
        },
        "order_summary": {
            "total_items": total_orders,
            "gross_amount_usd": gross_total,
            "settled_orders": paid_count,
        },
        "active_catalog_skus": [p["SKU"] for p in PRODUCTS_DATA],
    }
    
    pv.json(telemetry_payload, expanded=True)
