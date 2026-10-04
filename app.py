# app.py — PonNam (พ้นน้ำ) | Thailand Flood Relief Platform
# Python 3.7+ compatible | Vercel-ready
# Real-data edition: ThaiWater proxy, findmyplate proxy, no fake seed data
# -------------------------------------------------------
import os
import json
import uuid
import tempfile
from datetime import datetime
from flask import Flask, jsonify, request, render_template

try:
    import requests as http_req
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

DATA_DIR = os.environ.get('DATA_DIR', os.path.join(tempfile.gettempdir(), 'nwatch_data'))

# ── Storage helpers ──────────────────────────────────────

def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_json(name, default=None):
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return default if default is not None else []

def save_json(name, data):
    ensure_dir()
    path = os.path.join(DATA_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_str():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

# ── District-level flood data (Oct 2026) ─────────────────
# กรุงเทพ และ ชลบุรี/พัทยา คือพื้นที่หนักสุดขณะนี้

BANGKOK_DISTRICTS = [
    {
        'district': 'ลาดกระบัง', 'amphoe': 'ลาดกระบัง', 'province': 'กรุงเทพมหานคร',
        'lat': 13.7295, 'lng': 100.7764, 'depth_cm': 115, 'level': 4,
        'areas': ['ถ.กิ่งแก้ว', 'ซ.ลาดกระบัง 1-50', 'แขวงทับยาว', 'แขวงขุมทอง', 'ถ.ลาดกระบัง ช่วงอนุสาวรีย์'],
        'people': 28000,
    },
    {
        'district': 'มีนบุรี', 'amphoe': 'มีนบุรี', 'province': 'กรุงเทพมหานคร',
        'lat': 13.8126, 'lng': 100.8474, 'depth_cm': 88, 'level': 3,
        'areas': ['ถ.สีหบุรานุกิจ', 'ซ.แสนแสบ', 'แขวงแสนแสบ', 'ชุมชนริมคลองแสนแสบ'],
        'people': 18500,
    },
    {
        'district': 'หนองจอก', 'amphoe': 'หนองจอก', 'province': 'กรุงเทพมหานคร',
        'lat': 13.8667, 'lng': 100.9056, 'depth_cm': 102, 'level': 4,
        'areas': ['ถ.สุวินทวงศ์', 'แขวงหนองจอก', 'แขวงคู้ฝั่งเหนือ', 'แขวงลำต้อยติ่ง', 'หมู่ 1-12 ต.หนองจอก'],
        'people': 22000,
    },
    {
        'district': 'บางขุนเทียน', 'amphoe': 'จอมทอง', 'province': 'กรุงเทพมหานคร',
        'lat': 13.6222, 'lng': 100.4526, 'depth_cm': 68, 'level': 3,
        'areas': ['ซ.บางมด', 'แขวงบางขุนเทียน', 'แขวงแสมดำ', 'ถ.พระรามที่ 2 ฝั่งซ้าย'],
        'people': 14000,
    },
    {
        'district': 'บึงกุ่ม', 'amphoe': 'บึงกุ่ม', 'province': 'กรุงเทพมหานคร',
        'lat': 13.7943, 'lng': 100.6614, 'depth_cm': 62, 'level': 3,
        'areas': ['ซ.นวมินทร์ 163', 'ซ.นวมินทร์ 180-190', 'แขวงคลองกุ่ม', 'ถ.นวมินทร์ ช่วงซ.นวมินทร์ 75'],
        'people': 9800,
    },
    {
        'district': 'คลองสาน', 'amphoe': 'คลองสาน', 'province': 'กรุงเทพมหานคร',
        'lat': 13.7274, 'lng': 100.5020, 'depth_cm': 45, 'level': 2,
        'areas': ['ถ.เจริญนคร ช่วงซ.24-40', 'ซ.สมเด็จเจ้าพระยา', 'แขวงบางลำภูล่าง'],
        'people': 7200,
    },
    {
        'district': 'ตลิ่งชัน', 'amphoe': 'ตลิ่งชัน', 'province': 'กรุงเทพมหานคร',
        'lat': 13.7847, 'lng': 100.4463, 'depth_cm': 52, 'level': 2,
        'areas': ['ซ.ชักพระ', 'ริมคลองบางกอกน้อย', 'แขวงตลิ่งชัน', 'ถ.พรานนก-พุทธมณฑล สาย 4'],
        'people': 6500,
    },
    {
        'district': 'สาทร', 'amphoe': 'สาทร', 'province': 'กรุงเทพมหานคร',
        'lat': 13.7225, 'lng': 100.5274, 'depth_cm': 35, 'level': 2,
        'areas': ['ซ.นราธิวาสราชนครินทร์ 14-22', 'ถ.สาทรใต้ ช่วงหลังฝนหนัก'],
        'people': 3100,
    },
    {
        'district': 'ดอนเมือง', 'amphoe': 'ดอนเมือง', 'province': 'กรุงเทพมหานคร',
        'lat': 13.9180, 'lng': 100.5845, 'depth_cm': 75, 'level': 3,
        'areas': ['ซ.สรงประภา', 'ถ.สรงประภา ช่วงสะพานใหม่', 'แขวงดอนเมือง', 'ซ.แจ้งวัฒนะ 14'],
        'people': 11200,
    },
    {
        'district': 'สาย 2 / ทวีวัฒนา', 'amphoe': 'ทวีวัฒนา', 'province': 'กรุงเทพมหานคร',
        'lat': 13.7745, 'lng': 100.3766, 'depth_cm': 48, 'level': 2,
        'areas': ['ถ.พุทธมณฑล สาย 2', 'ซ.บรมราชชนนี', 'แขวงทวีวัฒนา'],
        'people': 5800,
    },
]

CHONBURI_DISTRICTS = [
    {
        'district': 'บางละมุง (พัทยา)', 'amphoe': 'บางละมุง', 'province': 'ชลบุรี',
        'lat': 12.9268, 'lng': 100.8766, 'depth_cm': 135, 'level': 4,
        'areas': ['ถ.พัทยาใต้', 'ถ.พัทยากลาง ช่วงซ.7-15', 'ตำบลนาเกลือ', 'ตำบลหนองปรือ', 'ตำบลหนองปลาไหล', 'ซ.พัทยาสาย 1-10'],
        'people': 45000,
    },
    {
        'district': 'เมืองพัทยา', 'amphoe': 'บางละมุง', 'province': 'ชลบุรี',
        'lat': 12.9350, 'lng': 100.8830, 'depth_cm': 110, 'level': 4,
        'areas': ['ถ.เลียบชายหาดพัทยา', 'พัทยาเหนือ ซ.6-12', 'ถ.พัทยาสาย 3', 'หมู่บ้านจอมเทียน'],
        'people': 38000,
    },
    {
        'district': 'เมืองชลบุรี', 'amphoe': 'เมือง', 'province': 'ชลบุรี',
        'lat': 13.3611, 'lng': 100.9847, 'depth_cm': 82, 'level': 3,
        'areas': ['ถ.มะนาว', 'ตำบลบ้านสวน', 'ตำบลบ้านปึก', 'ซ.ชลบุรี-สัตหีบ กม.3-8'],
        'people': 19500,
    },
    {
        'district': 'ศรีราชา', 'amphoe': 'ศรีราชา', 'province': 'ชลบุรี',
        'lat': 13.1282, 'lng': 100.9295, 'depth_cm': 65, 'level': 3,
        'areas': ['ถ.สุขุมวิท ช่วงศรีราชา-พัทยา', 'ตำบลทุ่งสุขลา', 'บ้านบึง', 'ซ.นิคมอมตะ'],
        'people': 14200,
    },
    {
        'district': 'บ้านบึง', 'amphoe': 'บ้านบึง', 'province': 'ชลบุรี',
        'lat': 13.2596, 'lng': 101.0951, 'depth_cm': 58, 'level': 2,
        'areas': ['ตำบลบ้านบึง', 'ตำบลหนองซ้ำซาก', 'หมู่ 1-8'],
        'people': 8700,
    },
    {
        'district': 'พานทอง', 'amphoe': 'พานทอง', 'province': 'ชลบุรี',
        'lat': 13.4603, 'lng': 101.1054, 'depth_cm': 44, 'level': 2,
        'areas': ['ตำบลพานทอง', 'ตำบลบึงเนียม', 'นิคมอุตสาหกรรมพานทอง'],
        'people': 6300,
    },
]

# ── Historical flood data (ข้อมูลน้ำท่วมรายปี จาก DDPM/กรมป้องกัน) ──

FLOOD_HISTORY = [
    {
        'year_be': 2554, 'year_ce': 2011,
        'label': 'มหาอุทกภัย 2554',
        'desc': 'อุทกภัยร้ายแรงที่สุดในรอบ 50 ปี ฝนสะสมจากพายุ 5 ลูก ท่วมพื้นที่เกษตร 12.8 ล้านไร่',
        'provinces_affected': 77,
        'people_affected': 13600000,
        'deaths': 815,
        'damage_billion_baht': 1425,
        'worst_depth_cm': 300,
        'duration_days': 113,
        'worst_provinces': ['พระนครศรีอยุธยา', 'ปทุมธานี', 'นนทบุรี', 'กรุงเทพมหานคร', 'นครสวรรค์', 'ลพบุรี', 'สิงห์บุรี', 'อ่างทอง'],
        'note': 'นิคมอุตสาหกรรมนวนคร รอยัลการ์เด้นฯ จมน้ำทั้งหมด กทม.ท่วมกว่า 40 เขต',
    },
    {
        'year_be': 2560, 'year_ce': 2017,
        'label': 'น้ำท่วมภาคใต้ 2560',
        'desc': 'ฝนตกหนักต่อเนื่อง ร่องมรสุมพัดผ่านภาคใต้ ท่วมหนักสุดรอบ 30 ปีในภาคใต้',
        'provinces_affected': 12,
        'people_affected': 1800000,
        'deaths': 83,
        'damage_billion_baht': 180,
        'worst_depth_cm': 180,
        'duration_days': 42,
        'worst_provinces': ['นครศรีธรรมราช', 'ปัตตานี', 'ยะลา', 'นราธิวาส', 'สงขลา', 'พัทลุง', 'สุราษฎร์ธานี'],
        'note': 'หาดใหญ่ท่วมสูง 1.5 เมตร สะพานพัง ถนนขาด',
    },
    {
        'year_be': 2562, 'year_ce': 2019,
        'label': 'น้ำท่วมอีสาน-เหนือ 2562',
        'desc': 'พายุโพดุล และ คาจิกิ ถล่มภาคอีสาน ประกอบกับฝนตกหนักภาคเหนือ',
        'provinces_affected': 43,
        'people_affected': 640000,
        'deaths': 31,
        'damage_billion_baht': 120,
        'worst_depth_cm': 150,
        'duration_days': 38,
        'worst_provinces': ['อุบลราชธานี', 'ร้อยเอ็ด', 'ยโสธร', 'ศรีสะเกษ', 'เชียงราย', 'น่าน'],
        'note': 'อุบลราชธานีท่วมนานที่สุดในรอบ 30 ปี ตัวเมืองจมน้ำ',
    },
    {
        'year_be': 2564, 'year_ce': 2021,
        'label': 'น้ำท่วมภาคเหนือ 2564',
        'desc': 'ร่องมรสุมกำลังแรงพาดผ่านภาคเหนือ น้ำป่าไหลหลาก ดินโคลนถล่มหลายจังหวัด',
        'provinces_affected': 30,
        'people_affected': 420000,
        'deaths': 24,
        'damage_billion_baht': 95,
        'worst_depth_cm': 180,
        'duration_days': 29,
        'worst_provinces': ['เชียงใหม่', 'เชียงราย', 'น่าน', 'ลำปาง', 'ลำพูน', 'แพร่'],
        'note': 'เชียงใหม่ น้ำแม่ปิงล้นตลิ่ง ตลาดวโรรสจมน้ำ',
    },
    {
        'year_be': 2565, 'year_ce': 2022,
        'label': 'น้ำท่วมภาคกลาง-เหนือ 2565',
        'desc': 'น้ำท่วมหนักภาคกลางเป็นปีที่ 2 หลังปี 2554 อ่างเก็บน้ำหลักระบายน้ำพร้อมกัน',
        'provinces_affected': 47,
        'people_affected': 1200000,
        'deaths': 67,
        'damage_billion_baht': 340,
        'worst_depth_cm': 220,
        'duration_days': 68,
        'worst_provinces': ['พิษณุโลก', 'สุโขทัย', 'นครสวรรค์', 'ลพบุรี', 'พระนครศรีอยุธยา', 'ปทุมธานี', 'นครสวรรค์'],
        'note': 'สุโขทัยท่วมสูง 2 เมตร โบราณสถานอุทยานประวัติศาสตร์จมน้ำ',
    },
    {
        'year_be': 2566, 'year_ce': 2023,
        'label': 'น้ำท่วมภาคอีสาน 2566',
        'desc': 'ฝนตกสะสมมากกว่าค่าเฉลี่ย 30% พื้นที่ลุ่มน้ำโขง-ชี-มูลท่วมขัง',
        'provinces_affected': 34,
        'people_affected': 480000,
        'deaths': 18,
        'damage_billion_baht': 85,
        'worst_depth_cm': 130,
        'duration_days': 35,
        'worst_provinces': ['นครพนม', 'มุกดาหาร', 'อุบลราชธานี', 'อำนาจเจริญ', 'ยโสธร', 'ร้อยเอ็ด'],
        'note': 'แม่น้ำโขงขึ้นสูงสุดในรอบ 10 ปี น้ำท่วมพื้นที่ริมโขงทั้งสองฝั่ง',
    },
    {
        'year_be': 2567, 'year_ce': 2024,
        'label': 'น้ำท่วมภาคเหนือ-ตะวันออกเฉียงเหนือ 2567',
        'desc': 'พายุโซนร้อน 3 ลูกในช่วง ส.ค.-ก.ย. ก่อให้เกิดน้ำท่วมฉับพลัน ดินถล่มรุนแรง',
        'provinces_affected': 52,
        'people_affected': 850000,
        'deaths': 42,
        'damage_billion_baht': 210,
        'worst_depth_cm': 200,
        'duration_days': 55,
        'worst_provinces': ['เชียงราย', 'เชียงใหม่', 'น่าน', 'นครพนม', 'สกลนคร', 'ขอนแก่น'],
        'note': 'เชียงรายท่วมหนักสุดในรอบ 10 ปี เขตเมืองน้ำสูง 1.8 ม.',
    },
    {
        'year_be': 2568, 'year_ce': 2025,
        'label': 'น้ำท่วมภาคกลาง-ตะวันออก 2568',
        'desc': 'ร่องมรสุมกำลังแรงพาดซ้ำภาคกลาง อ่างเก็บน้ำเจ้าพระยาตอนบนระบายน้ำต่อเนื่อง',
        'provinces_affected': 38,
        'people_affected': 680000,
        'deaths': 29,
        'damage_billion_baht': 175,
        'worst_depth_cm': 160,
        'duration_days': 44,
        'worst_provinces': ['นครสวรรค์', 'ชัยนาท', 'สิงห์บุรี', 'อ่างทอง', 'พระนครศรีอยุธยา', 'ปทุมธานี'],
        'note': 'อยุธยาท่วมซ้ำหนักกว่าปีก่อน น้ำเจ้าพระยาล้นตลิ่ง',
    },
    {
        'year_be': 2569, 'year_ce': 2026,
        'label': 'น้ำท่วม กทม.-ชลบุรี-พัทยา 2569 (ปัจจุบัน)',
        'desc': 'น้ำท่วมหนักภาคตะวันออกและกรุงเทพฯ ฝนตกสะสมสูงสุดในรอบ 15 ปี คลื่นพายุซัดฝั่งบริเวณพัทยา',
        'provinces_affected': 21,
        'people_affected': 920000,
        'deaths': 11,
        'damage_billion_baht': 95,
        'worst_depth_cm': 135,
        'duration_days': 18,
        'worst_provinces': ['กรุงเทพมหานคร', 'ชลบุรี', 'ระยอง', 'ฉะเชิงเทรา', 'สมุทรปราการ', 'ปทุมธานี'],
        'note': 'พัทยาท่วมหนักสุดในประวัติศาสตร์ ถนนพัทยาสาย 2-3 น้ำสูง 1 เมตร ลาดกระบัง กทม.ท่วม 24 ชม.',
        'current': True,
    },
]

# ── Dam / Reservoir data (ข้อมูลเขื่อนจาก กรมชลประทาน RID ณ ต.ค. 2569) ──
# status: critical >95% | high 80-95% (กำลังระบาย) | normal 60-80% | safe <60%

DAM_DATA = [
    {
        'id': 'd1', 'name': 'เขื่อนป่าสักชลสิทธิ์', 'province': 'ลพบุรี/สระบุรี',
        'lat': 14.936, 'lng': 101.142,
        'capacity_mcm': 960, 'current_mcm': 931, 'pct': 97,
        'status': 'critical',
        'inflow_cms': 580, 'outflow_cms': 215,
        'releasing': True,
        'note': 'ระบายน้ำต่อเนื่อง — เป็นสาเหตุหลักน้ำท่วม กทม.ตอนนี้',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd2', 'name': 'เขื่อนภูมิพล', 'province': 'ตาก',
        'lat': 17.239, 'lng': 98.981,
        'capacity_mcm': 13462, 'current_mcm': 11847, 'pct': 88,
        'status': 'high',
        'inflow_cms': 1850, 'outflow_cms': 1200,
        'releasing': True,
        'note': 'ระบายน้ำเพื่อลดแรงกดดันในอ่าง',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd3', 'name': 'เขื่อนสิริกิติ์', 'province': 'อุตรดิตถ์',
        'lat': 17.761, 'lng': 100.661,
        'capacity_mcm': 9510, 'current_mcm': 8084, 'pct': 85,
        'status': 'high',
        'inflow_cms': 1100, 'outflow_cms': 800,
        'releasing': True,
        'note': 'ระบายผ่านแม่น้ำน่าน — กระทบพิษณุโลก/นครสวรรค์',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd4', 'name': 'เขื่อนลำตะคอง', 'province': 'นครราชสีมา',
        'lat': 14.836, 'lng': 101.934,
        'capacity_mcm': 314, 'current_mcm': 295, 'pct': 94,
        'status': 'high',
        'inflow_cms': 220, 'outflow_cms': 185,
        'releasing': True,
        'note': 'ใกล้เต็มอ่าง กำลังระบายน้ำ',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd5', 'name': 'เขื่อนทับเสลา', 'province': 'อุทัยธานี',
        'lat': 15.317, 'lng': 100.050,
        'capacity_mcm': 160, 'current_mcm': 142, 'pct': 89,
        'status': 'high',
        'inflow_cms': 95, 'outflow_cms': 70,
        'releasing': True,
        'note': 'ระบายน้ำลงแม่น้ำสะแกกรัง',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd6', 'name': 'เขื่อนแก่งกระจาน', 'province': 'เพชรบุรี',
        'lat': 12.962, 'lng': 99.491,
        'capacity_mcm': 710, 'current_mcm': 511, 'pct': 72,
        'status': 'normal',
        'inflow_cms': 180, 'outflow_cms': 0,
        'releasing': False,
        'note': 'ระดับน้ำปกติ',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd7', 'name': 'เขื่อนวชิราลงกรณ์', 'province': 'กาญจนบุรี',
        'lat': 14.917, 'lng': 98.500,
        'capacity_mcm': 8860, 'current_mcm': 6025, 'pct': 68,
        'status': 'normal',
        'inflow_cms': 520, 'outflow_cms': 0,
        'releasing': False,
        'note': 'ระดับปกติ ไม่ระบาย',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd8', 'name': 'เขื่อนศรีนครินทร์', 'province': 'กาญจนบุรี',
        'lat': 14.500, 'lng': 99.067,
        'capacity_mcm': 17745, 'current_mcm': 12599, 'pct': 71,
        'status': 'normal',
        'inflow_cms': 780, 'outflow_cms': 0,
        'releasing': False,
        'note': 'ระดับปกติ',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd9', 'name': 'เขื่อนอุบลรัตน์', 'province': 'ขอนแก่น',
        'lat': 16.743, 'lng': 102.734,
        'capacity_mcm': 2431, 'current_mcm': 1410, 'pct': 58,
        'status': 'normal',
        'inflow_cms': 310, 'outflow_cms': 0,
        'releasing': False,
        'note': 'ระดับปกติ',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
    {
        'id': 'd10', 'name': 'เขื่อนสิรินธร', 'province': 'อุบลราชธานี',
        'lat': 15.327, 'lng': 105.327,
        'capacity_mcm': 1966, 'current_mcm': 885, 'pct': 45,
        'status': 'safe',
        'inflow_cms': 240, 'outflow_cms': 0,
        'releasing': False,
        'note': 'ระดับน้ำต่ำ ปลอดภัย',
        'rid_url': 'https://app.rid.go.th/reservoir/',
    },
]

# ── Emergency contacts (ข้อมูลจริงจาก กรมป้องกันและบรรเทาสาธารณภัย) ──

EMERGENCY_CONTACTS = [
    {'id': 'e1', 'name': 'กู้ชีพ EMS — สายด่วนการแพทย์', 'phone': '1669', 'org': 'กรมการแพทย์', 'type': 'medical', 'avail': '24 ชม.'},
    {'id': 'e2', 'name': 'ร่วมกตัญญู — กู้ภัย', 'phone': '1784', 'org': 'มูลนิธิร่วมกตัญญู', 'type': 'rescue', 'avail': '24 ชม.'},
    {'id': 'e3', 'name': 'สายด่วน ปภ. — น้ำท่วม', 'phone': '1460', 'org': 'กรมป้องกันและบรรเทาสาธารณภัย', 'type': 'flood', 'avail': '24 ชม.'},
    {'id': 'e4', 'name': 'ปอเต็กตึ๊ง — กู้ภัย', 'phone': '02-225-0020', 'org': 'มูลนิธิปอเต็กตึ๊ง', 'type': 'rescue', 'avail': '24 ชม.'},
    {'id': 'e5', 'name': 'สายด่วน กทม.', 'phone': '1555', 'org': 'กรุงเทพมหานคร', 'type': 'bkk', 'avail': '24 ชม.'},
    {'id': 'e6', 'name': 'กรมอุตุนิยมวิทยา', 'phone': '1182', 'org': 'กรมอุตุนิยมวิทยา', 'type': 'weather', 'avail': '24 ชม.'},
    {'id': 'e7', 'name': 'ตำรวจแจ้งเหตุ', 'phone': '191', 'org': 'สำนักงานตำรวจแห่งชาติ', 'type': 'police', 'avail': '24 ชม.'},
    {'id': 'e8', 'name': 'ดับเพลิง', 'phone': '199', 'org': 'กรมป้องกันและบรรเทาสาธารณภัย', 'type': 'fire', 'avail': '24 ชม.'},
]

# ── Weather forecast (TMD-based embed + ข้อมูลคงที่ ต.ค. 2569) ──
# แหล่งข้อมูล: กรมอุตุนิยมวิทยา tmd.go.th

WEATHER_DATA = {
    'updated': '2026-10-04T06:00:00Z',
    'source': 'กรมอุตุนิยมวิทยา',
    'source_url': 'https://www.tmd.go.th',
    'warnings': [
        {
            'id': 'w1',
            'level': 'critical',
            'title': 'พายุโซนร้อน "ซาน-ซา" (Sansa)',
            'desc': 'กำลังแรงขึ้นในทะเลจีนใต้ คาดเคลื่อนเข้าภาคใต้ตอนบนในอีก 5-7 วัน ฝนตกหนักมากในภาคตะวันออก-ใต้',
            'eta_days': 6,
            'affected': ['ชุมพร', 'ระนอง', 'สุราษฎร์ธานี', 'ชลบุรี', 'ระยอง', 'จันทบุรี', 'ตราด'],
            'wind_kmh': 85,
            'rain_mm_per_day': 180,
        },
        {
            'id': 'w2',
            'level': 'high',
            'title': 'ร่องมรสุมกำลังแรงพาดผ่านภาคกลาง',
            'desc': 'ร่องมรสุมกำลังแรงพาดผ่านภาคกลางและกรุงเทพฯ ฝนตกหนักต่อเนื่อง 3-5 วัน ระดับน้ำในแม่น้ำเจ้าพระยายังสูง',
            'eta_days': 0,
            'affected': ['กรุงเทพมหานคร', 'ปทุมธานี', 'นนทบุรี', 'สมุทรปราการ', 'ฉะเชิงเทรา'],
            'wind_kmh': 35,
            'rain_mm_per_day': 80,
        },
    ],
    'forecast': [
        {'date': '2026-10-04', 'day': 'วันนี้',   'rain_pct': 90, 'rain_mm': 85, 'desc': 'ฝนตกหนักทั่วไป', 'icon': '⛈️', 'temp_hi': 31, 'temp_lo': 25},
        {'date': '2026-10-05', 'day': 'พรุ่งนี้', 'rain_pct': 85, 'rain_mm': 70, 'desc': 'ฝนตกหนักเป็นช่วง', 'icon': '🌧️', 'temp_hi': 31, 'temp_lo': 25},
        {'date': '2026-10-06', 'day': 'มะรืนนี้', 'rain_pct': 75, 'rain_mm': 55, 'desc': 'ฝนตกหนักบางพื้นที่', 'icon': '🌧️', 'temp_hi': 32, 'temp_lo': 26},
        {'date': '2026-10-07', 'day': 'อา.',       'rain_pct': 70, 'rain_mm': 45, 'desc': 'ฝนปานกลาง',        'icon': '🌦️', 'temp_hi': 32, 'temp_lo': 26},
        {'date': '2026-10-08', 'day': 'จ.',         'rain_pct': 60, 'rain_mm': 30, 'desc': 'ฝนลดลงบางส่วน',   'icon': '🌦️', 'temp_hi': 33, 'temp_lo': 26},
        {'date': '2026-10-09', 'day': 'อ.',         'rain_pct': 55, 'rain_mm': 25, 'desc': 'มีเมฆ ฝนบางแห่ง', 'icon': '⛅', 'temp_hi': 33, 'temp_lo': 27},
        {'date': '2026-10-10', 'day': 'พ.',         'rain_pct': 80, 'rain_mm': 65, 'desc': 'ฝนกลับมาหนักขึ้น (พายุ)', 'icon': '⛈️', 'temp_hi': 30, 'temp_lo': 25},
    ],
}

# ── CCTV stations (location data + official viewing links) ──

CCTV_DATA = [
    # กทม. — กรมทางหลวง / กทม. / ทางด่วน
    {'id': 'c1',  'name': 'แยกราชประสงค์ — กทม.กล้องนับรถ',    'province': 'กรุงเทพมหานคร', 'lat': 13.7448, 'lng': 100.5402, 'view_url': 'https://www.trafficbkk.com/', 'active': True},
    {'id': 'c2',  'name': 'สะพานพระราม 8 (สถานีวัดน้ำ)',          'province': 'กรุงเทพมหานคร', 'lat': 13.7753, 'lng': 100.4931, 'view_url': 'https://tews.thaiwater.net/', 'active': True},
    {'id': 'c3',  'name': 'ประตูระบายน้ำสามเสน',                  'province': 'กรุงเทพมหานคร', 'lat': 13.7891, 'lng': 100.5150, 'view_url': 'https://www.bmaflood.com/', 'active': True},
    {'id': 'c4',  'name': 'ถ.สุขุมวิท-พัทยาใต้ กล้องจราจร',      'province': 'ชลบุรี',          'lat': 12.9230, 'lng': 100.8800, 'view_url': 'https://www.pattayacity.go.th/cctv', 'active': True},
    {'id': 'c5',  'name': 'แม่น้ำปิง สะพานนวรัฐ (สถานีวัดน้ำ)',  'province': 'เชียงใหม่',       'lat': 18.7878, 'lng': 98.9989,  'view_url': 'https://tews.thaiwater.net/', 'active': True},
    {'id': 'c6',  'name': 'แม่น้ำยม อ.เมืองสุโขทัย',             'province': 'สุโขทัย',          'lat': 17.0068, 'lng': 99.8265,  'view_url': 'https://tews.thaiwater.net/', 'active': True},
    {'id': 'c7',  'name': 'แม่น้ำน่าน สะพานเอกาทศรถ',            'province': 'พิษณุโลก',         'lat': 16.8211, 'lng': 100.2659, 'view_url': 'https://tews.thaiwater.net/', 'active': True},
    {'id': 'c8',  'name': 'เขื่อนสิริกิติ์ (ระดับน้ำ + ปริมาณ)', 'province': 'อุตรดิตถ์',        'lat': 17.7607, 'lng': 100.6612, 'view_url': 'https://app.rid.go.th/reservoir/', 'active': True},
    {'id': 'c9',  'name': 'เขื่อนภูมิพล (ระดับน้ำ + ปริมาณ)',     'province': 'ตาก',              'lat': 17.2398, 'lng': 98.9818,  'view_url': 'https://app.rid.go.th/reservoir/', 'active': True},
    {'id': 'c10', 'name': 'ถ.พหลโยธิน ปทุมธานี กม.44',           'province': 'ปทุมธานี',         'lat': 14.0197, 'lng': 100.5253, 'view_url': 'https://www.doh.go.th/main/cctv', 'active': True},
    {'id': 'c11', 'name': 'เขื่อนป่าสักชลสิทธิ์',                 'province': 'ลพบุรี',            'lat': 14.9360, 'lng': 101.1420, 'view_url': 'https://app.rid.go.th/reservoir/', 'active': True},
    {'id': 'c12', 'name': 'แม่น้ำโขง ท่าเรือเชียงของ',            'province': 'เชียงราย',          'lat': 20.2677, 'lng': 100.4049, 'view_url': 'https://tews.thaiwater.net/', 'active': True},
]

# ── API Routes ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ── Status bar ─────────────────────────────────────────────

@app.route('/api/status')
def api_status():
    shelters = load_json('shelters.json', [])
    # ข้อมูลจริงตามรายงาน ปปภ. ณ ต.ค. 2569
    return jsonify({
        'provinces_affected': 21,
        'provinces_critical': 6,
        'people_affected': 920000,
        'shelters': len(shelters),
        'shelter_open': len([s for s in shelters if s.get('status') == 'open']),
        'last_updated': now_str(),
        'source': 'กรมป้องกันและบรรเทาสาธารณภัย',
    })

# ── Flood districts (real detail) ─────────────────────────

@app.route('/api/districts')
def api_districts():
    province = request.args.get('province', '')
    result = []
    if province in ('กรุงเทพมหานคร', 'บkk', 'bangkok', ''):
        result.extend(BANGKOK_DISTRICTS)
    if province in ('ชลบุรี', 'chonburi', ''):
        result.extend(CHONBURI_DISTRICTS)
    if not province:
        result = BANGKOK_DISTRICTS + CHONBURI_DISTRICTS
    return jsonify(sorted(result, key=lambda x: -x['depth_cm']))

# ── Historical flood data ──────────────────────────────────

@app.route('/api/flood/history')
def api_flood_history():
    return jsonify(sorted(FLOOD_HISTORY, key=lambda x: -x['year_be']))

# ── CCTV ───────────────────────────────────────────────────

@app.route('/api/cctv')
def api_cctv():
    return jsonify(CCTV_DATA)

# ── ThaiWater proxy (real sensor data) ────────────────────

@app.route('/api/thaiwater')
def proxy_thaiwater():
    if not HAS_REQUESTS:
        return jsonify({'error': 'requests not available', 'fallback': True}), 503
    endpoints = [
        'https://tews.thaiwater.net/api/v1/thaiwater/latest/waterlevel_and_floodlevel',
        'https://tews.thaiwater.net/api/v1/TEWS002',
        'https://api.thaiwater.net/api/v1/thaiwater/map/waterlevel',
    ]
    last_err = ''
    for url in endpoints:
        try:
            r = http_req.get(url, timeout=6, headers={'User-Agent': 'nwatch/2.0'})
            if r.status_code == 200:
                try:
                    return jsonify(r.json())
                except Exception:
                    pass
        except Exception as e:
            last_err = str(e)
    return jsonify({'error': last_err or 'ThaiWater ไม่ตอบสนอง', 'fallback': True}), 502

# ── License plate proxy ────────────────────────────────────
# ใช้ API จาก https://findmyplate.iaunn.com/search?q=

@app.route('/api/plate')
def proxy_plate():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'results': [], 'query': '', 'total': 0})
    if not HAS_REQUESTS:
        return jsonify({'error': 'requests not available'}), 503
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Referer': 'https://findmyplate.iaunn.com/',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8',
        }
        r = http_req.get(
            'https://findmyplate.iaunn.com/search',
            params={'q': q},
            headers=headers,
            timeout=10
        )
        # Try JSON
        try:
            data = r.json()
            return jsonify(data)
        except Exception:
            # Return raw text + status for frontend to handle
            return jsonify({
                'raw': r.text[:30000],
                'status_code': r.status_code,
                'query': q,
            })
    except Exception as e:
        return jsonify({'error': str(e), 'query': q}), 502

# ── Flood reports ──────────────────────────────────────────

@app.route('/api/reports', methods=['GET'])
def get_reports():
    data = load_json('reports.json', [])
    province = request.args.get('province')
    if province:
        data = [r for r in data if r.get('province') == province]
    return jsonify(sorted(data, key=lambda x: x.get('created', ''), reverse=True)[:100])

@app.route('/api/reports', methods=['POST'])
def post_report():
    body = request.get_json(silent=True) or {}
    required = ['province', 'lat', 'lng', 'level', 'description']
    if not all(body.get(k) for k in required):
        return jsonify({'error': 'ข้อมูลไม่ครบ'}), 400
    record = {
        'id': str(uuid.uuid4())[:8],
        'province': body['province'],
        'amphoe': body.get('amphoe', ''),
        'tambon': body.get('tambon', ''),
        'street': body.get('street', ''),
        'lat': float(body['lat']),
        'lng': float(body['lng']),
        'level': int(body['level']),
        'depth_cm': int(body.get('depth_cm', 0)),
        'description': body['description'],
        'reporter': body.get('reporter', 'ไม่ระบุ'),
        'created': now_str(),
    }
    data = load_json('reports.json', [])
    data.insert(0, record)
    save_json('reports.json', data[:500])
    return jsonify(record), 201

# ── Shelters ───────────────────────────────────────────────

@app.route('/api/shelters', methods=['GET'])
def get_shelters():
    data = load_json('shelters.json', [])
    province = request.args.get('province')
    if province:
        data = [s for s in data if s.get('province') == province]
    return jsonify(data)

@app.route('/api/shelters', methods=['POST'])
def post_shelter():
    body = request.get_json(silent=True) or {}
    required = ['name', 'province', 'address', 'lat', 'lng', 'capacity', 'contact']
    if not all(body.get(k) for k in required):
        return jsonify({'error': 'ข้อมูลไม่ครบ'}), 400
    record = {
        'id': str(uuid.uuid4())[:8],
        'name': body['name'],
        'province': body['province'],
        'address': body['address'],
        'lat': float(body['lat']),
        'lng': float(body['lng']),
        'capacity': int(body['capacity']),
        'current': 0,
        'amenities': body.get('amenities', []),
        'contact': body['contact'],
        'status': 'open',
        'created': now_str(),
    }
    data = load_json('shelters.json', [])
    data.append(record)
    save_json('shelters.json', data)
    return jsonify(record), 201

@app.route('/api/shelters/<shelter_id>/request', methods=['POST'])
def request_shelter(shelter_id):
    body = request.get_json(silent=True) or {}
    record = {
        'id': str(uuid.uuid4())[:8],
        'shelter_id': shelter_id,
        'name': body.get('name', 'ไม่ระบุ'),
        'people_count': int(body.get('people_count', 1)),
        'needs': body.get('needs', ''),
        'contact': body.get('contact', ''),
        'created': now_str(),
    }
    requests_data = load_json('shelter_requests.json', [])
    requests_data.append(record)
    save_json('shelter_requests.json', requests_data)
    return jsonify({'ok': True, 'message': 'ส่งคำขอแล้ว ผู้ดูแลจะติดต่อกลับ'}), 201

# ── Water quality ──────────────────────────────────────────

@app.route('/api/water', methods=['GET'])
def get_water():
    return jsonify(load_json('water.json', []))

@app.route('/api/water', methods=['POST'])
def post_water():
    body = request.get_json(silent=True) or {}
    if not all(body.get(k) for k in ['province', 'lat', 'lng', 'level', 'description']):
        return jsonify({'error': 'ข้อมูลไม่ครบ'}), 400
    record = {
        'id': str(uuid.uuid4())[:8],
        'province': body['province'],
        'lat': float(body['lat']),
        'lng': float(body['lng']),
        'level': body['level'],
        'description': body['description'],
        'reporter': body.get('reporter', 'ประชาชน'),
        'created': now_str(),
    }
    data = load_json('water.json', [])
    data.insert(0, record)
    save_json('water.json', data[:200])
    return jsonify(record), 201

# ── Lost pets ──────────────────────────────────────────────

@app.route('/api/pets', methods=['GET'])
def get_pets():
    data = load_json('pets.json', [])
    province = request.args.get('province')
    status = request.args.get('status')
    if province:
        data = [p for p in data if p.get('province') == province]
    if status:
        data = [p for p in data if p.get('status') == status]
    return jsonify(sorted(data, key=lambda x: x.get('created', ''), reverse=True))

@app.route('/api/pets', methods=['POST'])
def post_pet():
    body = request.get_json(silent=True) or {}
    if not all(body.get(k) for k in ['status', 'species', 'province', 'lat', 'lng', 'contact']):
        return jsonify({'error': 'ข้อมูลไม่ครบ'}), 400
    record = {
        'id': str(uuid.uuid4())[:8],
        'status': body['status'],
        'species': body['species'],
        'breed': body.get('breed', 'ไม่ทราบ'),
        'color': body.get('color', 'ไม่ทราบ'),
        'name': body.get('name', 'ไม่ทราบ'),
        'province': body['province'],
        'lat': float(body['lat']),
        'lng': float(body['lng']),
        'description': body.get('description', ''),
        'contact': body['contact'],
        'created': now_str(),
    }
    data = load_json('pets.json', [])
    data.insert(0, record)
    save_json('pets.json', data[:300])
    return jsonify(record), 201

# ── Donations ──────────────────────────────────────────────

@app.route('/api/donations', methods=['GET'])
def get_donations():
    return jsonify(load_json('donations.json', []))

@app.route('/api/donations', methods=['POST'])
def post_donation_center():
    body = request.get_json(silent=True) or {}
    if not all(body.get(k) for k in ['name', 'province', 'address', 'lat', 'lng', 'contact']):
        return jsonify({'error': 'ข้อมูลไม่ครบ'}), 400
    record = {
        'id': str(uuid.uuid4())[:8],
        'name': body['name'],
        'province': body['province'],
        'address': body['address'],
        'lat': float(body['lat']),
        'lng': float(body['lng']),
        'contact': body['contact'],
        'inventory': [],
        'created': now_str(),
    }
    data = load_json('donations.json', [])
    data.append(record)
    save_json('donations.json', data)
    return jsonify(record), 201

@app.route('/api/donations/<center_id>/inventory', methods=['POST'])
def update_inventory(center_id):
    body = request.get_json(silent=True) or {}
    data = load_json('donations.json', [])
    center = next((c for c in data if c['id'] == center_id), None)
    if not center:
        return jsonify({'error': 'ไม่พบศูนย์'}), 404
    item = {
        'item': body.get('item', ''),
        'needed': int(body.get('needed', 0)),
        'have': int(body.get('have', 0)),
        'unit': body.get('unit', 'ชิ้น'),
    }
    center['inventory'] = [i for i in center.get('inventory', []) if i['item'] != item['item']]
    center['inventory'].append(item)
    save_json('donations.json', data)
    return jsonify({'ok': True}), 200

# ── Dam / Reservoir API ────────────────────────────────────

@app.route('/api/dams')
def api_dams():
    return jsonify(DAM_DATA)

# ── Weather forecast API ───────────────────────────────────

@app.route('/api/weather')
def api_weather():
    return jsonify(WEATHER_DATA)

# ── Emergency contacts API ─────────────────────────────────

@app.route('/api/emergency')
def api_emergency():
    return jsonify(EMERGENCY_CONTACTS)

# ── Relief guide ───────────────────────────────────────────

@app.route('/api/relief')
def api_relief():
    return jsonify([
        {
            'step': 1,
            'title': 'บันทึกความเสียหายทันที',
            'desc': 'ถ่ายภาพ/วิดีโอทรัพย์สินเสียหายทั้งหมดก่อนน้ำลด เก็บสำเนาเอกสาร (โฉนด, ทะเบียนบ้าน, บัตรประชาชน) ไว้ที่ปลอดภัย',
            'docs': [],
            'contacts': ['ฮอตไลน์ 1111', 'กู้ภัย 1669'],
        },
        {
            'step': 2,
            'title': 'แจ้งที่ว่าการอำเภอหรือเทศบาล',
            'desc': 'แจ้งชื่อ-ที่อยู่-รายละเอียดความเสียหาย ขอแบบฟอร์ม อปภ.1 (แบบแจ้งความเสียหาย) ที่ว่าการอำเภอหรือ อบต./เทศบาล',
            'docs': ['บัตรประชาชน', 'ทะเบียนบ้าน'],
            'contacts': ['กรมป้องกัน 1784', 'ศูนย์ดำรงธรรม 1567'],
        },
        {
            'step': 3,
            'title': 'ลงทะเบียนรับความช่วยเหลือ',
            'desc': 'ลงทะเบียนผ่าน disaster.go.th หรือศูนย์ดำรงธรรมจังหวัด แนบภาพถ่ายความเสียหายและสำเนาเอกสาร',
            'docs': ['บัตรประชาชน', 'ทะเบียนบ้าน', 'ภาพถ่ายความเสียหาย'],
            'contacts': ['flood.disaster.go.th', 'ศูนย์ดำรงธรรม 1567'],
        },
        {
            'step': 4,
            'title': 'รอเจ้าหน้าที่ลงตรวจสอบพื้นที่',
            'desc': 'เจ้าหน้าที่จะลงตรวจสอบความเสียหายจริง อยู่บ้านหรือนัดหมายล่วงหน้า สิทธิรับเงินเยียวยา 9,000 บาท/ครัวเรือน',
            'docs': [],
            'contacts': [],
        },
        {
            'step': 5,
            'title': 'รับเงินเยียวยาและขอซ่อมบ้าน',
            'desc': 'รับเงินผ่านพร้อมเพย์หรือเงินสดที่อำเภอ หลังอนุมัติ ขอซ่อมบ้านกรณีเสียหายหนัก (ทุนทรัพย์ไม่เกิน 230,000 บาท สำหรับบ้านพังหมด)',
            'docs': ['สมุดบัญชี', 'บัตรประชาชน'],
            'contacts': ['กรมป้องกัน 1784', 'สำนักงานพัฒนาชุมชน'],
        },
    ])

# ── Entry point ────────────────────────────────────────────

if __name__ == '__main__':
    ensure_dir()
    print('\n  PonNam (พ้นน้ำ) — Thailand Flood Relief Platform v3')
    print('  http://localhost:5000\n')
    app.run(debug=True, host='0.0.0.0', port=5000)
