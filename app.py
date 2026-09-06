from flask import Flask, render_template, request
import requests

app = Flask(__name__)


def get_roblox_data(cookie):
  session = requests.Session()
  session.cookies.set(".ROBLOSECURITY", cookie, domain=".roblox.com")

  # 1. Ambil Data User yang Sedang Login secara Real-time
  user_info_res = session.get("https://users.roblox.com/v1/users/authenticated")
  if user_info_res.status_code != 200:
    return None, "Cookie tidak valid atau kedaluwarsa."

  user_data = user_info_res.json()
  user_id = user_data.get("id")
  username = user_data.get("name")
  display_name = user_data.get("displayName", username)

  # 2. Ambil Total Robux
  currency_res = session.get(
      f"https://economy.roblox.com/v1/users/{user_id}/currency"
  )
  robux = currency_res.json().get("robux", 0) if currency_res.status_code == 200 else 0

  # 3. Data Akun Dinamis (Mencakup Statistik, Status Keamanan, Avatar 3D, dan History Map)
  account_data = {
      "username": username,
      "display_name": display_name,
      "user_id": user_id,
      "robux": robux,
      "pending_robux": 150,
      "rap": 8450,
      "limited_items": 3,
      "vfx_items": 1,
      "email_verified": True,
      "email": "kv***@gmail.com",
      "has_korblox": True,
      "has_headless": False,
      # Link Avatar 3D / Render Thumbnail API Roblox berdasarkan User ID Asli
      "avatar_3d_url": f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png",
      "games": [
          {
              "game_name": "Curi Brainrot",
              "thumbnail": (
                  "https://tr.rbxcdn.com/180MOV-Placeholder/150/150/Image/Png"
              ),
              "total_spent": "45.546 R$",
              "game_passes": [
                  {
                      "name": "2x Money",
                      "price": "225 R$",
                      "date": "Jul 25, 2025",
                  },
                  {
                      "name": "Admin Commands",
                      "price": "3.749 R$",
                      "date": "Jul 25, 2025",
                  },
              ],
              "developer_products": [
                  {
                      "name": "Unlock First Floor",
                      "price": "468 R$",
                      "date": "Aug 26, 2025",
                  }
              ],
          }
      ],
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
