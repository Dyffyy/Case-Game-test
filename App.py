import streamlit as st
import random
from streamlit_server_state import server_state, server_state_lock

# Konfigurasi paparan fon (Mobile Friendly)
st.set_page_config(page_title="Clue Online", page_icon="🕵️‍♂️", layout="centered")

# 1. SETUP GLOBAL SERVER STATE (Otak Utama Server)
if "rooms" not in server_state:
    with server_state_lock["rooms"]:
        server_state["rooms"] = {}

# Senarai Kad Asal
WEAPONS = ["Pistol", "Tali", "Lilin", "Pisau"]
ROOMS = ["Dining room", "Living room", "Kitchen", "Hall", "Spa"]
SUSPECTS = ["Green", "White", "Plum", "Mustard", "Peacock", "Scarlet"]

# 2. LOGIK BLOK GAME (DIPROSES DI SERVER)
def inisialkan_game(room_code):
    with server_state_lock["rooms"]:
        room = server_state["rooms"][room_code]
        
        # Pilih Case Card Rahsia
        case_weapon = random.choice(WEAPONS)
        case_room = random.choice(ROOMS)
        case_suspect = random.choice(SUSPECTS)
        
        room["case_cards"] = {"weapon": case_weapon, "room": case_room, "suspect": case_suspect}
        
        # Kumpul & gaul baki kad
        remaining = []
        remaining.extend([w for w in WEAPONS if w != case_weapon])
        remaining.extend([r for r in ROOMS if r != case_room])
        remaining.extend([s for s in SUSPECTS if s != case_suspect])
        random.shuffle(remaining)
        
        # Agih kad kepada player secara sekata
        players = room["players"]
        player_hands = {name: [] for name in players}
        for i, card in enumerate(remaining):
            p_idx = i % len(players)
            player_hands[players[p_idx]].append(card)
            
        room["player_hands"] = player_hands
        room["turn"] = 0
        room["status"] = "PLAYING"
        room["logs"].append("🎮 Game bermula! Kad telah diagihkan secara rahsia.")

# 3. INTERFACE PENGGUNA (UI FOR PHONE)
st.title("🕵️‍♂️ Detektif Clue Online")
st.write("Main game detektif bersama rakan-rakan secara online!")

# Simpan status player secara lokal di fon masing-masing
if "my_name" not in st.session_state:
    st.session_state.my_name = ""
if "my_room" not in st.session_state:
    st.session_state.my_room = ""
if "joined" not in st.session_state:
    st.session_state.joined = False

# BUTTON REFRESH (Penting untuk fon update situasi terkini game)
st.button("🔄 Refresh Skrin / Update Game")

# PENGURUSAN LOG IN / MASUK BILIK
if not st.session_state.joined:
    st.subheader("🚪 Masuk atau Buat Bilik Baru")
    name_input = st.text_input("Nama Anda:", value=st.session_state.my_name).strip()
    room_input = st.text_input("Kod Bilik (Contoh: GENG99):", value=st.session_state.my_room).strip().upper()
    
    if st.button("Masuk Bilik 🚀"):
        if name_input and room_input:
            st.session_state.my_name = name_input
            st.session_state.my_room = room_input
            st.session_state.joined = True
            
            with server_state_lock["rooms"]:
                if room_input not in server_state["rooms"]:
                    # Kalau bilik belum wujud, create baru (Dia jadi Host)
                    server_state["rooms"][room_input] = {
                        "status": "LOBBY",
                        "host": name_input,
                        "players": [name_input],
                        "case_cards": {},
                        "player_hands": {},
                        "turn": 0,
                        "logs": [f"➕ {name_input} telah mencipta bilik."]
                    }
                else:
                    # Kalau bilik dah ada, check nama klon
                    if name_input not in server_state["rooms"][room_input]["players"]:
                        server_state["rooms"][room_input]["players"].append(name_input)
                        server_state["rooms"][room_input]["logs"].append(f"👋 {name_input} masuk ke bilik.")
            st.rerun()
        else:
            st.error("Sila isi Nama dan Kod Bilik!")
else:
    # JIKA PLAYER DAH BERJAYA MASUK BILIK
    room_id = st.session_state.my_room
    user_name = st.session_state.my_name
    
    # Check jika bilik tiba-tiba hilang/error
    if room_id not in server_state["rooms"]:
        st.error("Bilik tidak wujud.")
        st.session_state.joined = False
        st.rerun()
        
    room_data = server_state["rooms"][room_id]
    
    # PAPARAN HEADER KETIKA DALAM GAME
    st.info(f"📍 Bilik: **{room_id}** | 🧑 Anda: **{user_name}** (Host: {room_data['host']})")
    
    # ------------------ SKRIN LOBBY (MENUNGGU PEMAIN) ------------------
    if room_data["status"] == "LOBBY":
        st.subheader("👥 Senarai Pemain Dalam Bilik:")
        for p in room_data["players"]:
            st.write(f"• {p}")
            
        if user_name == room_data["host"]:
            if len(room_data["players"]) >= 2:
                if st.button("🚀 MULAKAN GAME SEKARANG", type="primary"):
                    inisialkan_game(room_id)
                    st.rerun()
            else:
                st.warning("Menunggu sekurang-kurangnya 2 orang pemain untuk mula...")
        else:
            st.warning("Menunggu Host untuk memulakan game. Sila tekan button 'Refresh' di atas jika skrin lambat lambat.")
            
    # ------------------ SKRIN UTAMA GAMEPLAY ------------------
    elif room_data["status"] == "PLAYING":
        # Ambil giliran siapa sekarang
        current_turn_player = room_data["players"][room_data["turn"]]
        
        # 1. Papar Kad Sendiri (Rahsia kat fon sendiri je!)
        my_hand = room_data["player_hands"].get(user_name, [])
        st.subheader("🃏 Kad Di Tangan Anda (RAHSIA):")
        st.success(", ".join(my_hand) if my_hand else "Tiada kad")
        
        st.markdown("---")
        
        # 2. Status Giliran Semasa
        if current_turn_player == user_name:
            st.subheader("🎯 GILIRAN ANDA KINI!")
            
            # Borang Buat Tekaan
            g_suspect = st.selectbox("Pilih Suspect:", SUSPECTS)
            g_weapon = st.selectbox("Pilih Weapon:", WEAPONS)
            g_room = st.selectbox("Pilih Room:", ROOMS)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Teka Pusingan 🧪", use_container_width=True):
                    # Proses semakan tekaan pusingan biasa
                    tekaan = [g_suspect, g_weapon, g_room]
                    catatan_log = f"🤔 {user_name} menuduh [{g_suspect} + {g_weapon} + {g_room}]. Hasilnya: "
                    
                    hasil_semakan = []
                    for kad in tekaan:
                        siapa_ada = None
                        for p, hand in room_data["player_hands"].items():
                            if p != user_name and kad in hand:
                                siapa_ada = p
                                break
                        if siapa_ada:
                            hasil_semakan.append(f"❌ Kad [{kad}] ada pada tangan {siapa_ada}.")
                        elif kad in my_hand:
                            hasil_semakan.append(f"ℹ️ Kad [{kad}] ada kat tangan anda sendiri.")
                        else:
                            hasil_semakan.append(f"❓ Kad [{kad}] MISTERI (Tiada siapa pegang)!")
                    
                    full_log = catatan_log + " | ".join(hasil_semakan)
                    
                    with server_state_lock["rooms"]:
                        server_state["rooms"][room_id]["logs"].append(full_log)
                        # Tukar giliran
                        server_state["rooms"][room_id]["turn"] = (room_data["turn"] + 1) % len(room_data["players"])
                    st.rerun()
                    
            with col2:
                if st.button("🚨 TUDUHAN AKHIR 🚨", type="primary", use_container_width=True):
                    # Semak kes penjenayah rahsia sebenar
                    cases = room_data["case_cards"]
                    with server_state_lock["rooms"]:
                        if g_suspect == cases["suspect"] and g_weapon == cases["weapon"] and g_room == cases["room"]:
                            server_state["rooms"][room_id]["status"] = "TAMAT"
                            server_state["rooms"][room_id]["logs"].append(f"🎉 TAHNIAH! {user_name} berjaya selesaikan kes! Pembunuh ialah {cases['suspect']} guna {cases['weapon']} di {cases['room']}.")
                        else:
                            server_state["rooms"][room_id]["logs"].append(f"💀 {user_name} membuat Tuduhan Akhir yang SALAH! Pembunuh sebenar masih bebas.")
                            server_state["rooms"][room_id]["turn"] = (room_data["turn"] + 1) % len(room_data["players"])
                    st.rerun()
        else:
            st.subheader(f"⏳ Giliran: **{current_turn_player.upper()}** sedang berfikir...")
            st.info("Sila borak/tanya secara bersemuka atau tunggu log dikemas kini.")
            
        st.markdown("---")
        
        # 3. Papan Log Kes (Semua orang boleh tengok perkembangan clue)
        st.subheader("📝 Buku Log Detektif (Clue Tracker):")
        for log in reversed(room_data["logs"]):
            st.write(log)
            
    # ------------------ SKRIN GAME TAMAT ------------------
    elif room_data["status"] == "TAMAT":
        st.header("🏁 GAME OVER 🏁")
        for log in reversed(room_data["logs"]):
            st.write(log)
            
        if st.button("Keluar Bilik / Main Lagi"):
            st.session_state.joined = False
            st.rerun()
