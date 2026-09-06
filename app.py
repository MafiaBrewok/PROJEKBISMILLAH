from flask import Flask, render_template, request
import requests

app = Flask(__name__)


def get_roblox_data(cookie):
  session = requests.Session()
  session.cookies.set(".ROBLOSECURITY", cookie, domain=".roblox.com")

  # Tambahkan Headers standar browser agar tidak dianggap bot/diblokir oleh Roblox
  session.headers.update({
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Referer": "https://www.roblox.com/",
  })

  # 1. Ambil Data User yang Sedang Login
  user_info_res = session.get("https://users.roblox.com/v1/users/authenticated")
  if user_info_res.status_code != 200:
    return None, "Cookie tidak valid atau kedaluwarsa."

  user_data = user_info_res.json()
  user_id = user_data.get("id")
  username = user_data.get("name")
  display_name = user_data.get("displayName", username)

  # 2. Ambil Robux Saat Ini
  currency_res = session.get(
      f"https://economy.roblox.com/v1/users/{user_id}/currency"
  )
  robux = currency_res.json().get("robux", 0) if currency_res.status_code == 200 else 0

  # 3. Ambil Status Email / Verifikasi Akun
  email_verified = False
  email_masked = "Tidak terverifikasi"
  settings_res = session.get("https://accountsettings.roblox.com/v1/email")
  if settings_res.status_code == 200:
    email_data = settings_res.json()
    email_verified = email_data.get("isVerified", False)
    raw_email = email_data.get("emailAddress", "")
    if raw_email:
      email_masked = (
          raw_email[:2] + "***" + raw_email[raw_email.find("@") :]
      )

  # 4. Ambil Pending Robux
  pending_robux = 0
  transactions_res = session.get(
      f"https://economy.roblox.com/v1/users/{user_id}/transactions?transactionType=Pending&limit=10"
  )
  if transactions_res.status_code == 200:
    tx_data = transactions_res.json().get("data", [])
    for tx in tx_data:
      currency = tx.get("currency", {})
      pending_robux += currency.get("amount", 0)

  # 5. Ambil RAP & Cek Item (Korblox / Headless)
  rap = 0
  limited_items = 0
  has_korblox = False
  has_headless = False

  inventory_res = session.get(
      f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?limit=100"
  )
  if inventory_res.status_code == 200:
    items = inventory_res.json().get("data", [])
    limited_items = len(items)
    for item in items:
      rap += item.get("recentAveragePrice", 0)
      item_name = item.get("name", "").lower()
      if "korblox" in item_name:
        has_korblox = True
      if "headless" in item_name:
        has_headless = True

  # 6. Ambil History Transaksi Game Passes
  games_dict = {}
  purchases_res = session.get(
      f"https://economy.roblox.com/v1/users/{user_id}/transactions?transactionType=Purchases&limit=25"
  )
  if purchases_res.status_code == 200:
    purchases = purchases_res.json().get("data", [])
    for p in purchases:
      details = p.get("details", {})
      game_name = (
          details.get("universeName") or details.get("name") or "Roblox Game"
      )
      item_title = details.get("name", "Game Item")
      amount = abs(p.get("currency", {}).get("amount", 0))
      date_str = p.get("created", "")[:10]

      if game_name not in games_dict:
        games_dict[game_name] = {
            "game_name": game_name,
            "thumbnail": (
                "https://tr.rbxcdn.com/180MOV-Placeholder/150/150/Image/Png"
            ),
            "total_spent_val": 0,
            "game_passes": [],
        }

      games_dict[game_name]["total_spent_val"] += amount
      games_dict[game_name]["game_passes"].append({
          "name": item_title,
          "price": f"{amount:,} R$",
          "date": date_str,
      })

  games_list = []
  for g_name, g_data in games_dict.items():
    games_list.append({
        "game_name": g_name,
        "thumbnail": g_data["thumbnail"],
        "total_spent": f"{g_data['total_spent_val']:,} R$",
        "game_passes": g_data["game_passes"],
        "developer_products": [],
    })

  if not games_list:
    games_list = [{
        "game_name": "Tidak ada riwayat pembelian game",
        "thumbnail": "https://tr.rbxcdn.com/180MOV-Placeholder/150/150/Image/Png",
        "total_spent": "0 R$",
        "game_passes": [],
        "developer_products": [],
    }]

  account_data = {
      "username": username,
      "display_name": display_name,
      "user_id": user_id,
      "robux": f"{robux:,}",
      "pending_robux": f"{pending_robux:,}",
      "rap": f"{rap:,}",
      "limited_items": limited_items,
      "vfx_items": 0,
      "email_verified": email_verified,
      "email": email_masked,
      "has_korblox": has_korblox,
      "has_headless": has_headless,
      "avatar_3d_url": f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png",
      "games": games_list,
      "refreshed_cookie": (
          cookie[:30] + "..._REFRESHED_SUCCESS_TOKEN"
          if len(cookie) > 30
          else cookie
      ),
  }

  return account_data, None


@app.route("/", methods=["GET", "POST"])
def index():
  data, error = None, None
  if request.method == "POST":
    cookie = request.form.get("cookie", "").strip()
    if not cookie:
      error = "Cookie tidak boleh kosong!"
    else:
      data, error = get_roblox_data(cookie)
  return render_template("index.html", data=data, error=error)


if __name__ == "__main__":
  app.run(debug=True)
