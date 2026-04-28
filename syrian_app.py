import streamlit as st
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------
# الاتصال بقاعدة البيانات
# --------------------------------------------
def get_connection():
    postgresql://neondb_owner:npg_o5AUFeRY0bEc@ep-orange-heart-alzvcg78-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
        database="names_db",
        user="postgres",
        password="admin01"
    )

# --------------------------------------------
# إعدادات الصفحة
# --------------------------------------------
st.set_page_config(page_title="نظام إدارة العسكريين السوريين", page_icon="🇸🇾", layout="wide")

st.markdown("# 🇸🇾 نظام إدارة العسكريين السوريين")
st.markdown("---")

# القائمة الجانبية
menu = st.sidebar.radio(
    "القائمة الرئيسية",
    [
        "➕ إضافة عسكري جديد",
        "📋 عرض جميع العسكريين",
        "🔍 بحث متقدم",
        "🗑️ حذف عسكري",
        "📊 إحصائيات"
    ]
)

# --------------------------------------------
# 1. إضافة عسكري جديد
# --------------------------------------------
if menu == "➕ إضافة عسكري جديد":
    st.subheader("➕ إضافة عسكري سوري جديد")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("الاسم الثلاثي *")
            mother_name = st.text_input("اسم الأم *")
            rank = st.selectbox("الرتبة *", [
                "جندي", "عريف", "رقيب", "مساعد", "ملازم", "ملازم أول",
                "نقيب", "رائد", "مقدم", "عقيد", "عميد", "لواء", "فريق"
            ])

        with col2:
            residence = st.text_input("مكان السكن *")
            details = st.text_area("التفاصيل", height=150,
                                  placeholder="يمكنك كتابة ملاحظات تصل إلى 2000 حرف...")

        submitted = st.form_submit_button("💾 حفظ البيانات", type="primary")

        if submitted:
            if full_name.strip() and mother_name.strip() and residence.strip():
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO syrian_military (full_name, mother_name, residence, rank, details)
                    VALUES (%s, %s, %s, %s, %s)
                """, (full_name, mother_name, residence, rank, details))
                conn.commit()
                conn.close()
                st.success(f"✅ تم إضافة {full_name} بنجاح")
            else:
                st.error("❌ الاسم الثلاثي، اسم الأم، ومكان السكن مطلوبة")

# --------------------------------------------
# 2. عرض جميع العسكريين
# --------------------------------------------
elif menu == "📋 عرض جميع العسكريين":
    st.subheader("📋 قائمة العسكريين السوريين")

    conn = get_connection()
    df = pd.read_sql("""
        SELECT id, full_name, mother_name, residence, rank, details, created_at
        FROM syrian_military
        ORDER BY id DESC
    """, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True, height=500)
        st.info(f"📌 إجمالي المسجلين: {len(df)}")
    else:
        st.warning("لا يوجد عسكريون مسجلون")

# --------------------------------------------
# 3. بحث متقدم
# --------------------------------------------
elif menu == "🔍 بحث متقدم":
    st.subheader("🔍 البحث في قاعدة العسكريين")

    col1, col2 = st.columns(2)
    with col1:
        search_name = st.text_input("بحث بالاسم الثلاثي")
    with col2:
        search_rank = st.selectbox("بحث بالرتبة",
            ["الكل", "جندي", "عريف", "رقيب", "مساعد", "ملازم", "ملازم أول",
             "نقيب", "رائد", "مقدم", "عقيد", "عميد", "لواء", "فريق"])

    if st.button("🔎 ابحث"):
        conn = get_connection()
        if search_rank == "الكل":
            df = pd.read_sql("""
                SELECT * FROM syrian_military
                WHERE full_name ILIKE %s
            """, conn, params=(f"%{search_name}%",))
        else:
            df = pd.read_sql("""
                SELECT * FROM syrian_military
                WHERE full_name ILIKE %s AND rank = %s
            """, conn, params=(f"%{search_name}%", search_rank))
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.success(f"✅ تم العثور على {len(df)} نتيجة")
        else:
            st.warning("❌ لم يتم العثور على نتائج")

# --------------------------------------------
# 4. حذف عسكري
# --------------------------------------------
elif menu == "🗑️ حذف عسكري":
    st.subheader("🗑️ حذف عسكري من القاعدة")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, rank FROM syrian_military ORDER BY full_name")
    people = cur.fetchall()
    conn.close()

    if people:
        options = {}
        for p in people:
            options[f"{p[1]} (الرتبة: {p[2]})"] = p[0]
        selected = st.selectbox("اختر العسكري المراد حذفه", list(options.keys()))

        if st.button("🗑️ تأكيد الحذف", type="secondary"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM syrian_military WHERE id = %s", (options[selected],))
            conn.commit()
            conn.close()
            st.success(f"✅ تم حذف {selected.split(' (')[0]} بنجاح")
            st.rerun()
    else:
        st.info("لا يوجد عسكريون للحذف")

# --------------------------------------------
# 5. إحصائيات
# --------------------------------------------
elif menu == "📊 إحصائيات":
    st.subheader("📊 إحصائيات العسكريين السوريين")

    conn = get_connection()
    total = pd.read_sql("SELECT COUNT(*) as total FROM syrian_military", conn)["total"][0]
    ranks_stats = pd.read_sql("""
        SELECT rank, COUNT(*) as count
        FROM syrian_military
        GROUP BY rank
        ORDER BY count DESC
    """, conn)
    conn.close()

    col1, col2 = st.columns(2)
    col1.metric("👥 إجمالي العسكريين", f"{total:,}")
    col2.metric("🎖️ عدد الرتب المختلفة", len(ranks_stats))

    if not ranks_stats.empty:
        st.subheader("📊 توزيع العسكريين حسب الرتبة")
        fig, ax = plt.subplots()
        ax.barh(ranks_stats['rank'], ranks_stats['count'], color='darkgreen')
        ax.set_xlabel('العدد')
        ax.set_title('توزيع الرتب')
        st.pyplot(fig)