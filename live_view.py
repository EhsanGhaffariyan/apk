import flet as ft
import requests

def live_view(page: ft.Page):
    page.title = "Country Channel Selector"
    page.scroll = "auto"
    page.bgcolor = "#090B7C"
    page.padding = 20

    loading_ring = ft.ProgressRing(visible=True)
    page.add(loading_ring)

    countries_url = 'https://iptv-org.github.io/api/countries.json'
    try:
        countries_response = requests.get(countries_url)
        countries_response.raise_for_status()
        countries_data = countries_response.json()
    except requests.RequestException as e:
        page.add(ft.Text(f"Error fetching countries data: {e}", color=ft.Colors.WHITE))
        return

    name_to_code = {country["name"]: country["code"].lower() for country in countries_data}

    m3u_url = 'https://iptv-org.github.io/iptv/index.country.m3u'
    try:
        m3u_response = requests.get(m3u_url)
        m3u_response.raise_for_status()
        m3u_content = m3u_response.text
    except requests.RequestException as e:
        page.add(ft.Text(f"Error fetching M3U file: {e}", color=ft.Colors.WHITE))
        return

    country_channels = {}
    lines = m3u_content.splitlines()
    for i in range(len(lines)):
        line = lines[i]
        if line.startswith('#EXTINF'):
            parts = line.split('group-title="')
            if len(parts) > 1:
                country = parts[1].split('"')[0]
                channel_name = line.split(',', 1)[1] if ',' in line else "Unnamed Channel"
                logo = line.split('tvg-logo="')[1].split('"')[0] if 'tvg-logo="' in line else "https://via.placeholder.com/64"
                url = lines[i + 1].strip() if (i + 1 < len(lines) and not lines[i + 1].startswith('#')) else ""
                if country not in country_channels:
                    country_channels[country] = []
                country_channels[country].append({"name": channel_name, "logo": logo, "url": url})

    loading_ring.visible = False
    page.update()

    top_bar = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=ft.Colors.WHITE,
                on_click=lambda e: page.go("/"),
            ),
            ft.Image(src="logo.png", height=40)
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10
    )

    country_grid = ft.GridView(
        runs_count=9,
        child_aspect_ratio=0.8,
        spacing=10,
        padding=10,
        expand=True,
    )

    for country in sorted(country_channels.keys()):
        code = name_to_code.get(country)
        flag_url = f"https://flagcdn.com/36x27/{code}.png"
        country_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(src=flag_url, width=36, height=27),
                    ft.Text(country, size=16, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            padding=5,
            bgcolor=ft.Colors.BLUE,
            border_radius=5,
            alignment=ft.alignment.center,
            on_click=lambda e, cnt=country: show_country_channels(page, cnt, country_channels[cnt]),
        )
        country_grid.controls.append(country_container)

    page_content = ft.Column(
        controls=[
            top_bar,
            country_grid
        ],
        spacing=20,
        expand=True
    )

    page.controls.clear()
    page.controls.append(page_content)
    page.update()

def show_country_channels(page: ft.Page, country: str, channels: list):
    """Display a country's channels with a video player in a sidebar, ProgressBar, and search functionality"""
    page.title = f"Channels - {country}"
    page.bgcolor = "#090B7C"
    page.padding = 20

    def show_message(message):
        page.snackbar = ft.SnackBar(content=ft.Text(message))
        page.update()

    if not channels:
        page.add(ft.Text(f"No channels found for {country}", color=ft.Colors.WHITE))
        page.update()
        return

    top_bar = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=ft.Colors.WHITE,
                on_click=lambda e: live_view(page),
            ),
            ft.Text(f"{country}", size=20, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10
    )

    # فیلد جستجو
    search_field = ft.TextField(
        label="Search Channels",
        width=300,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,
        on_change=lambda e: update_channel_list(e.control.value)
    )

    progress_bar = ft.ProgressBar(
        width=200,
        color=ft.Colors.BLUE,
        bgcolor=ft.Colors.GREY_800,
        visible=True
    )

    video_player = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Select a channel to play", color=ft.Colors.WHITE, size=16),
                progress_bar
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor=ft.Colors.BLACK,
        border_radius=10,
        alignment=ft.alignment.center,
        height=400,
        width=600
    )

    channel_grid = ft.GridView(
        runs_count=4,
        child_aspect_ratio=0.8,
        spacing=10,
        padding=10,
        height=400,
        width=300
    )

    # تابع برای به‌روزرسانی لیست کانال‌ها بر اساس جستجو
    def update_channel_list(search_query: str):
        channel_grid.controls.clear()
        filtered_channels = [
            channel for channel in channels
            if search_query.lower() in channel["name"].lower() or not search_query
        ]
        for channel in filtered_channels:
            logo_src = channel["logo"] if channel["logo"] and channel["logo"].strip() else "https://via.placeholder.com/64"
            def play_channel(e, url=channel["url"]):
                progress_bar.visible = True
                video_player.content = ft.Column(
                    controls=[progress_bar],
                    alignment=ft.MainAxisAlignment.CENTER
                )
                page.update()

                video_player.content = ft.Video(
                    expand=True,
                    playlist=[ft.VideoMedia(url)],
                    playlist_mode=ft.PlaylistMode.LOOP,
                    autoplay=True,
                    volume=100,
                    aspect_ratio=16/9,
                    show_controls=True,
                    filter_quality=ft.FilterQuality.HIGH,
                    muted=False,
                    on_enter_fullscreen=lambda e: show_message("Video entered fullscreen!"),
                    on_exit_fullscreen=lambda e: show_message("Video exited fullscreen!"),
                    on_loaded=lambda e: (
                        setattr(progress_bar, "visible", False),
                        page.update()
                    ),
                    on_error=lambda e: (
                        setattr(video_player, "content", ft.Text(f"Playback error: {e.data}", color=ft.Colors.RED)),
                        page.update()
                    )
                )
                page.update()

            channel_container = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Image(src=logo_src, width=64, height=64, fit=ft.ImageFit.COVER),
                        ft.Text(channel["name"], size=14, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5
                ),
                padding=5,
                bgcolor=ft.Colors.GREY_900,
                border_radius=10,
                alignment=ft.alignment.center,
                on_click=play_channel
            )
            channel_grid.controls.append(channel_container)
        page.update()

    # نمایش اولیه تمام کانال‌ها
    update_channel_list("")

    page_content = ft.Column(
        controls=[
            top_bar,
            ft.Row(
                controls=[search_field],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            ft.Row(
                controls=[
                    channel_grid,
                    video_player
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            )
        ],
        spacing=20,
    )

    page.controls.clear()
    page.controls.append(page_content)
    page.update()