from nicegui import ui, app
import sqlite3
import asyncio
import locale
from datetime import datetime

# --- AYARLAR ---
PROJE_ISMI = "EkHesap"
SPLASH_SURESI = 3.34

try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
except:
    pass

# --- VERİTABANI BAŞLATMA ---
def init_db():
    with sqlite3.connect("butce.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS harcamalar (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, miktar REAL, kategori TEXT, tur TEXT, tarih TEXT, ay_yil TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS notlar (id INTEGER PRIMARY KEY AUTOINCREMENT, icerik TEXT, tarih TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS ayarlar (anahtar TEXT PRIMARY KEY, deger TEXT)")

def get_dil():
    try:
        with sqlite3.connect("butce.db") as conn:
            res = conn.execute("SELECT deger FROM ayarlar WHERE anahtar = 'dil'").fetchone()
            return res[0] if res else None
    except: return None

init_db()

KAT_BILGI = {
    'Mutfak': 'restaurant', 'Kira': 'home', 'Eğlence': 'confirmation_number', 
    'Maaş': 'payments', 'Ulaşım': 'directions_bus', 'Diğer': 'category'
}

@ui.page('/')
async def main_page():
    AKTIF_DIL = get_dil() or 'tr'
    T = {
        'tr': {'bakiye': 'Toplam Varlık', 'gelir': 'Kazanç', 'gider': 'Harcama', 'ekle': 'Yeni İşlem', 'kaydet': 'ONAYLA', 'notlar': 'Notlarım', 'analiz': 'Raporlar'},
        'en': {'bakiye': 'Total Assets', 'gelir': 'Income', 'gider': 'Expense', 'ekle': 'Add Transaction', 'kaydet': 'CONFIRM', 'notlar': 'Notes', 'analiz': 'Analytics'}
    }[AKTIF_DIL]

    # --- 1. SPLASH SCREEN ---
    splash = ui.column().classes('fixed inset-0 w-full h-full bg-[#0a0a0b] items-center justify-center z-[2000]')
    with splash:
        ui.icon('wallet', size='100px', color='indigo-500').classes('animate-pulse')
        ui.label(PROJE_ISMI).classes('text-white text-5xl font-black tracking-tighter mt-4')
    ui.timer(SPLASH_SURESI, lambda: splash.delete(), once=True)

    # --- 2. TEMA ---
    ui.query('body').style('background-color: #0f1115; color: #e2e8f0; font-family: "Inter", sans-serif;')
    container = ui.column().classes('w-full max-w-md mx-auto pb-32 pt-10 px-6')

    def sayfa_degistir(sayfa_adi):
        container.clear()
        with container:
            if sayfa_adi == 'home': home_view()
            elif sayfa_adi == 'stats': stats_view()
            elif sayfa_adi == 'notes': notes_view()
            elif sayfa_adi == 'dev': dev_view()

    # --- 3. SAYFALAR ---
    
    def home_view():
        ui.label(datetime.now().strftime("%A, %d %B").upper()).classes('text-slate-500 text-[10px] font-black tracking-widest mb-2 px-2')
        
        @ui.refreshable
        def bakiye_kart():
            ay_yil = datetime.now().strftime("%m.%Y")
            with sqlite3.connect("butce.db") as conn:
                gelir = conn.execute("SELECT SUM(miktar) FROM harcamalar WHERE tur LIKE '%Kazanç%' AND ay_yil=?", (ay_yil,)).fetchone()[0] or 0
                gider = conn.execute("SELECT SUM(miktar) FROM harcamalar WHERE tur LIKE '%Harcama%' AND ay_yil=?", (ay_yil,)).fetchone()[0] or 0
            
            with ui.card().classes('w-full p-8 rounded-[2.5rem] bg-gradient-to-br from-[#1e1e2e] to-[#0f1115] border border-white/5 shadow-2xl mb-8'):
                ui.label(T['bakiye']).classes('text-indigo-400/60 text-[10px] font-bold uppercase tracking-widest')
                ui.label(f'{(gelir - gider):,.2f} TL').classes('text-4xl font-black mt-2 tracking-tighter text-white')
                with ui.row().classes('w-full justify-between mt-8 pt-6 border-t border-white/5'):
                    ui.label(f'↑ {gelir:,.0f}').classes('text-emerald-400 font-bold text-sm')
                    ui.label(f'↓ {gider:,.0f}').classes('text-rose-400 font-bold text-sm')
        
        @ui.refreshable
        def harcama_listesi():
            ui.label('HAREKETLER').classes('text-slate-500 text-[10px] font-black tracking-widest mb-4 px-2')
            with sqlite3.connect("butce.db") as conn:
                rows = conn.execute("SELECT id, isim, miktar, kategori, tur, tarih FROM harcamalar ORDER BY id DESC LIMIT 15").fetchall()
                for r_id, isim, miktar, kat, tur, tarih in rows:
                    renk = 'emerald-400' if 'Kazanç' in tur else 'rose-400'
                    with ui.card().classes('w-full mb-3 rounded-2xl bg-[#1a1c23] border border-white/5 shadow-sm p-3'):
                        with ui.row().classes('w-full items-center justify-between'):
                            with ui.row().classes('items-center gap-3'):
                                ui.avatar(KAT_BILGI.get(kat, 'category'), color='indigo-900', text_color='indigo-300').classes('rounded-xl').style('width:32px; height:32px')
                                with ui.column().classes('gap-0'):
                                    ui.label(isim).classes('font-bold text-slate-200 text-sm')
                                    ui.label(tarih).classes('text-[9px] text-slate-500')
                            with ui.row().classes('items-center gap-2'):
                                ui.label(f'{miktar:,.0f}').classes(f'font-black text-{renk} text-sm')
                                # SİLME BUTONU
                                ui.button(icon='delete', on_click=lambda x, i=r_id: [sqlite3.connect("butce.db").execute("DELETE FROM harcamalar WHERE id=?", (i,)).connection.commit(), sayfa_degistir('home')]).props('flat round dense color=grey-8').classes('scale-75')
        
        bakiye_kart(); harcama_listesi()

    def stats_view():
        ui.label(T['analiz']).classes('text-3xl font-black mb-6 tracking-tighter')
        ay_yil = datetime.now().strftime("%m.%Y")
        with sqlite3.connect("butce.db") as conn:
            gelir = conn.execute("SELECT SUM(miktar) FROM harcamalar WHERE tur LIKE '%Kazanç%' AND ay_yil=?", (ay_yil,)).fetchone()[0] or 0
            gider = conn.execute("SELECT SUM(miktar) FROM harcamalar WHERE tur LIKE '%Harcama%' AND ay_yil=?", (ay_yil,)).fetchone()[0] or 0
        
        with ui.card().classes('w-full p-6 rounded-[2.5rem] bg-[#1a1c23] border border-white/5 shadow-xl'):
            ui.echart({
                'series': [{'type': 'pie', 'radius': ['60%', '80%'], 'data': [
                    {'value': gelir, 'name': T['gelir'], 'itemStyle': {'color': '#34d399'}},
                    {'value': gider, 'name': T['gider'], 'itemStyle': {'color': '#fb7185'}}
                ], 'label': {'show': True, 'color': '#fff'}}]
            }).classes('h-72 w-full')

    def notes_view():
        ui.label(T['notlar']).classes('text-3xl font-black mb-6 tracking-tighter text-white')
        with ui.row().classes('w-full mb-6 gap-2'):
            n_i = ui.input(placeholder='Hızlı not...').classes('flex-grow dark').props('dark standout rounded')
            def not_kaydet():
                if n_i.value:
                    with sqlite3.connect("butce.db") as conn:
                        conn.execute("INSERT INTO notlar (icerik, tarih) VALUES (?, ?)", (n_i.value, datetime.now().strftime("%d.%m %H:%M")))
                    n_i.value = ''; sayfa_degistir('notes')
            ui.button(icon='send', on_click=not_kaydet).props('round color=indigo-600')

        with sqlite3.connect("butce.db") as conn:
            notlar = conn.execute("SELECT id, icerik, tarih FROM notlar ORDER BY id DESC").fetchall()
            for nid, icerik, tarih in notlar:
                with ui.card().classes('w-full mb-3 bg-[#1a1c23] border border-white/5 rounded-2xl'):
                    with ui.row().classes('w-full justify-between items-center'):
                        with ui.column().classes('gap-0'):
                            ui.label(icerik).classes('text-slate-200 font-bold')
                            ui.label(tarih).classes('text-[9px] text-slate-500')
                        ui.button(icon='delete', on_click=lambda x, i=nid: [sqlite3.connect("butce.db").execute("DELETE FROM notlar WHERE id=?", (i,)).connection.commit(), sayfa_degistir('notes')]).props('flat round dense color=grey-8')

    def dev_view():
        with ui.column().classes('w-full items-center text-center gap-6 pt-10'):
            ui.avatar('settings_suggest', size='100px', color='indigo-600', text_color='white').classes('shadow-2xl')
            ui.label(f'{PROJE_ISMI} v7.1').classes('text-3xl font-black text-white')
            with ui.column().classes('w-full gap-4 px-6'):
                ui.button('Geliştirici: efkwn38', on_click=lambda: ui.navigate.to('https://instagram.com/efkwn38', new_tab=True)).classes('w-full bg-[#1a1c23] border border-white/10 rounded-2xl py-4 font-black text-sm').props('no-caps icon=photo_camera')
                ui.button('Stüdyo: efkwnlabs', on_click=lambda: ui.navigate.to('https://instagram.com/efkwnlabs', new_tab=True)).classes('w-full bg-indigo-600 text-white rounded-2xl py-4 font-black shadow-lg shadow-indigo-500/20 text-sm').props('no-caps icon=rocket_launch')

    # --- 4. EKLEME DİYALOĞU ---
    with ui.dialog() as ekle_dialog, ui.card().classes('bg-[#1a1c23] p-8 rounded-[3rem] w-80 border border-white/10'):
        ui.label(T['ekle']).classes('text-white text-2xl font-black mb-6 tracking-tighter')
        tur_s = ui.select([T['gider'], T['gelir']], value=T['gider']).classes('w-full mb-4 dark').props('dark standout rounded')
        isim_i = ui.input('Açıklama').classes('w-full mb-4').props('dark standout rounded')
        mikt_i = ui.number('Tutar').classes('w-full mb-4').props('dark standout rounded')
        kat_s = ui.select(list(KAT_BILGI.keys()), value='Diğer').classes('w-full mb-6 dark').props('dark standout rounded')
        
        async def islem_kaydet():
            if isim_i.value and mikt_i.value:
                with sqlite3.connect("butce.db") as conn:
                    conn.execute("INSERT INTO harcamalar (isim, miktar, kategori, tur, tarih, ay_yil) VALUES (?, ?, ?, ?, ?, ?)", 
                                (isim_i.value, mikt_i.value, kat_s.value, tur_s.value, datetime.now().strftime("%d.%m.%Y %H:%M"), datetime.now().strftime("%m.%Y")))
                ekle_dialog.close(); sayfa_degistir('home')
        ui.button(T['kaydet'], on_click=islem_kaydet).classes('w-full bg-indigo-600 text-white rounded-2xl py-4 font-black')

    # --- 5. COMPACT GLASS DOCK (MOBİL UYUMLU) ---
    with ui.footer().classes('bg-transparent border-none flex flex-col items-center pb-6'):
        ui.button(icon='add', on_click=ekle_dialog.open).props('round size=20px color=indigo-600 shadow-2xl').classes('mb-[-24px] z-[100] active:scale-90 transition-all')
        with ui.row().classes('bg-[#1a1c23]/80 backdrop-blur-3xl rounded-[2.5rem] px-6 py-3 shadow-2xl border border-white/10 items-center gap-6'):
            ui.button(icon='home', on_click=lambda: sayfa_degistir('home')).props('flat round color=slate-400 size=md')
            ui.button(icon='analytics', on_click=lambda: sayfa_degistir('stats')).props('flat round color=slate-400 size=md')
            ui.button(icon='draw', on_click=lambda: sayfa_degistir('notes')).props('flat round color=slate-400 size=md')
            ui.button(icon='person', on_click=lambda: sayfa_degistir('dev')).props('flat round color=slate-400 size=md')

    sayfa_degistir('home')

    if get_dil() is None:
        with ui.dialog() as d, ui.card().classes('bg-[#0f1115] p-10 rounded-[3rem] items-center border border-white/10'):
            ui.label(PROJE_ISMI).classes('text-white text-4xl font-black mb-8 tracking-tighter')
            with ui.row().classes('gap-4'):
                ui.button('TR', on_click=lambda: [sqlite3.connect("butce.db").execute("INSERT INTO ayarlar VALUES('dil','tr')").connection.commit(), ui.navigate.to('/')]).classes('bg-white text-black rounded-xl px-8 py-3 font-black')
                ui.button('EN', on_click=lambda: [sqlite3.connect("butce.db").execute("INSERT INTO ayarlar VALUES('dil','en')").connection.commit(), ui.navigate.to('/')]).classes('bg-indigo-600 text-white rounded-xl px-8 py-3 font-black')
        d.open()

ui.run(title='EkHesap Premium', port=8080)