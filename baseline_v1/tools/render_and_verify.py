"""Print the guide, verify local replay, and render review pages."""
from pathlib import Path
import json,re,hashlib
import fitz
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'review';O.mkdir(exist_ok=True)
report={}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,channel='msedge')
    page=browser.new_page(viewport={'width':1200,'height':900})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((R/'Tutorial_A_to_Z.html').as_uri());page.emulate_media(media='print')
    page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
    sizes=page.locator('.page').evaluate_all('(els)=>els.map((e,i)=>({page:i+1,height:e.getBoundingClientRect().height,scroll:e.scrollHeight}))')
    report['guide_sections']=sizes
    page.pdf(path=str(R/'Tutorial_A_to_Z.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
    page.emulate_media(media='screen');page.goto((R/'index.html').as_uri())
    page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
    before=page.locator('#status').inner_text()
    page.locator('#step').fill('5');page.locator('#step').dispatch_event('input')
    assert page.locator('#status').inner_text()!=before
    page.select_option('#policy','raw');assert page.locator('#step').input_value()=='0'
    page.click('#play');page.wait_for_timeout(420);assert int(page.locator('#step').input_value())>0;page.click('#play')
    page.screenshot(path=str(O/'project_desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(O/'project_mobile.png'),full_page=True)
    report['replay']={'scrubber':True,'policy_selector':True,'play_pause':True,'javascript_errors':errors}
    browser.close()
doc=fitz.open(R/'Tutorial_A_to_Z.pdf')
report['pdf_pages']=len(doc);report['words']=sum(len(p.get_text().split()) for p in doc)
report['outside_page_blocks']=[]
for i,page in enumerate(doc):
    for block in page.get_text('blocks'):
        if block[0]<-1 or block[1]<-1 or block[2]>page.rect.width+1 or block[3]>page.rect.height+1:
            report['outside_page_blocks'].append(i+1)
    if i in (0,2,3,8,10,12,19,20,len(doc)-1):page.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(O/f'guide_{i+1:02}.png')
report['hardware_tested']=False
(O/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
assert not errors
