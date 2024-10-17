from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
import time
from urllib.request import Request, urlopen
import excelwriter as excel

def get_driver():
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument("--incognito")
  chrome_options.add_argument("--disable-extensions")  
  chrome_options.add_argument("--dns-prefetch-disable")
  chrome_options.page_load_strategy = 'none'
  driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=chrome_options)
  return driver

def get_stats(section):
  stats = dict()
  for event in section.find_all('div', attrs={'data-testid':'wcl-statistics'}):
    data_div = event.find('div', class_='_category_18zuy_15')
    stats[data_div.find('div', attrs={'data-testid':'wcl-statistics-category'}).find('strong').text] = {
      'home': data_div.find('div', class_='_homeValue_7ptpb_9').find('strong').text,
      'away':  data_div.find('div', class_='_awayValue_7ptpb_13').find('strong').text 
    }
  return stats

def get_comments(driver):
  driver.find_element(By.XPATH, '//a[@href="#/resumen-del-partido/comentarios-en-directo"]').click()
  WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "liveCommentary"))
    )
  html_data = driver.page_source
  soup_game_page = BeautifulSoup(html_data, 'lxml')
  comments = soup_game_page.find("div", class_ = "liveCommentary")
  list_comments = []
  for item, comment in enumerate(comments.find_all('div', attrs={'data-testid':'wcl-commentary'})):
    if len(comment.find_all('div', attrs={'data-testid':'wcl-commentary-headline-text'})) == 1:
      title = comment.find('div', attrs={'data-testid':'wcl-commentary-headline-text'}).find('strong').text.replace("'","")
    else:
      title = ''
    if len(comment.find_all('div',attrs={'data-testid':'wcl-commentaryTitle-general'})) == 1:
      detail = comment.find('div', attrs={'data-testid':'wcl-commentaryTitle-general'}).find(attrs={'data-testid': 'wcl-scores-simpleText2'}).text
    elif len(comment.find_all('div',attrs={'data-testid':'wcl-commentaryTitle-highlighted'})) == 1:
      detail = comment.find('div', attrs={'data-testid':'wcl-commentaryTitle-highlighted'}).find(attrs={'data-testid': 'wcl-scores-simpleText2'}).text
    list_comments.append({
      'title': title,
      'details': detail
    })
  return list_comments

def get_player_data(player):
  url = Request(player['player_link'], headers={'User-Agent': 'Mozilla/5.0'})
  html_page = urlopen(url).read()
  soup = BeautifulSoup(html_page, 'html.parser')
  player_header = soup.find('div', id='player-profile-heading')
  player['country'] = player_header.find('ol', class_="_breadcrumbList_11l8j_10").find_all('span', recursive=False)[1].text
  player['full_name'] = player_header.find('div', class_="playerHeader__wrapper").find('div', class_="playerHeader__nameWrapper").text
  if player_header.find('div', class_="playerHeader__wrapper").find('div', class_="playerInfoItem") != None and len(player_header.find('div', class_="playerHeader__wrapper").find('div', class_="playerInfoItem").find_all('span', class_="_webTypeSimpleText01_1loh2_8")) > 0:
    player['birthdate'] = str(player_header.find('div', class_="playerHeader__wrapper").find('div', class_="playerInfoItem").find_all('span', class_="_webTypeSimpleText01_1loh2_8")[1].text).replace("(","").replace(")","")
  return player

if __name__ == "__main__":
  driver = get_driver()
  driver.get('https://www.flashscore.com.mx/futbol/espana/laliga-ea-sports/resultados/')
  print('Loading Main Div...')
  WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sportName"))
    )
  html_data = driver.page_source
  soup_main_page = BeautifulSoup(html_data, 'lxml')
  div_rounds = soup_main_page.find("div", class_ = "sportName soccer")
  list_games_round9 = []
  is_round9 = False
  print('Collecting games...')
  for game_div in div_rounds.find_all('div'):
    if 'event__round' in game_div['class'] and 'event__round--static' in game_div['class'] and game_div.string == 'Jornada 9':
      is_round9 = True
    if 'event__round' in game_div['class'] and 'event__round--static' in game_div['class'] and game_div.string != 'Jornada 9':
      is_round9 = False
    if is_round9 and 'event__match--static' in game_div['class'] and 'event__match--twoLine' in game_div['class']:
      # Game from round 9
      id = game_div.get('id')
      game_anchor = game_div.find('a', attrs={'aria-describedby': id})
      list_games_round9.append({
        'id': id,
        'game_link': game_anchor['href'],
        'event_time': game_div.find('div', class_ = 'event__time').string,
        'home_team': game_div.find('div', class_='event__homeParticipant').find(attrs={'data-testid': 'wcl-scores-simpleText1'}).text,
        'away_team': game_div.find('div', class_='event__awayParticipant').find(attrs={'data-testid': 'wcl-scores-simpleText1'}).text,
        'home_team_score': game_div.find('div', class_ = 'event__score--home').text,
        'away_team_score': game_div.find('div', class_ = 'event__score--away').text
      })
  for idx, game in enumerate(list_games_round9):
  # for idx, game in enumerate(list_games_round9[:2]):
    print(f"Collecting details of game {game['id']}")
    driver.get(game['game_link'])
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CLASS_NAME, "smv__verticalSections"))
    )
    # Get RESUMEN
    print('Collecting SUMMARY...')
    html_data = driver.page_source
    soup_game_page = BeautifulSoup(html_data, 'lxml')
    game['summary'] = []
    smv__verticalSections = soup_game_page.find('div', class_ = 'smv__verticalSections')
    for item in smv__verticalSections.find_all('div', class_="smv__participantRow"):
      if 'smv__awayParticipant' in item['class']:
        team = 'away'
      elif 'smv__homeParticipant' in item['class']:
        team = 'home'
      else:
        raise 'No team found'
      event_time = str(item.find('div', class_='smv__timeBox').text).replace("'","")
      second_player = ''
      second_player_link = ''
      incident = item.find('div', class_='smv__incident')
      if len(incident.find_all('div', class_="smv__incidentIconSub")) > 0:
        # Susbtitution
        event = 'substitucion'
        main_player = incident.find('a', class_='smv__playerName').text
        main_player_link = incident.find('a', class_='smv__playerName')['href']
        second_player = incident.find('a', class_='smv__subDown').text
        second_player_link = incident.find('a', class_='smv__subDown')['href']
      elif len(incident.find('div', class_="smv__incidentIcon").find_all('div', class_='smv__incidentHomeScore')) > 0 or len(incident.find('div', class_="smv__incidentIcon").find_all('div', class_='smv__incidentAwayScore')) > 0:
        # Goal
        event = 'gol'
        main_player = incident.find('a', class_='smv__playerName').text
        main_player_link = incident.find('a', class_='smv__playerName')['href']
        if len(incident.find_all('div', class_="smv__assist")) > 0:
          # There is assister
          second_player = incident.find('div', class_='smv__assist').find('a').text
          second_player_link = incident.find('div', class_='smv__assist').find('a')['href']
      elif len(incident.find('div', class_="smv__incidentIcon").find_all('svg', class_='warning')) > 0:
        # Missed penalty
        event = 'penalti_fallado'
        main_player = incident.find('a', class_='smv__playerName').text
        main_player_link = incident.find('a', class_='smv__playerName')['href']
      elif len(incident.find('div', class_="smv__incidentIcon").find_all('svg', class_='yellowCard-ico')) > 0:
        # Yellow card
        event = 'tarjeta_amarilla'
        main_player = incident.find('a', class_='smv__playerName').text
        main_player_link = incident.find('a', class_='smv__playerName')['href']
      elif len(incident.find('div', class_="smv__incidentIcon").find_all('svg', class_='redCard-ico')) > 0:
        # Direct Red card
        event = 'tarjeta_roja'
        main_player = incident.find('a', class_='smv__playerName').text
        main_player_link = incident.find('a', class_='smv__playerName')['href']
      elif len(incident.find('div', class_="smv__incidentIcon").find_all('svg', class_='card-ico')) > 0: 
        # Double Yellow card
        event = '2da_tarjeta_amarilla'
        main_player = incident.find('a', class_='smv__playerName').text
        main_player_link = incident.find('a', class_='smv__playerName')['href']
      elif len(incident.find('div', class_="smv__incidentIcon").find_all('svg', class_='var')) > 0 and len(incident.find_all('div', string="Gol anulado - fuera de juego")) > 0:
        # Var Gol anulado
        event = "gol_anulado_offside"
        main_player = incident.find('div', class_='smv__assist').find('a').text
        main_player_link = incident.find('div', class_='smv__assist').find('a')['href']
      # event div
      row = {
        'team': team,
        'time': event_time,
        'event': event,
        'main_player': main_player,
        'main_player_link': main_player_link,
        'second_player': second_player,
        'second_player_link': second_player_link
      }
      if 'event' in globals():
        del event
      if 'event_time' in globals():
        del event_time
      if 'team' in globals():
        del team
      if 'main_player' in globals():
        del main_player  
      if 'second_player' in globals():
        del second_player
      game['summary'].append(row)
    # Get ESTADISTICAS
    print('Collecting STATS...')
    game['stats'] = dict()
    driver.find_element(By.XPATH, '//a[@href="#/resumen-del-partido/estadisticas-del-partido"]').click()
    WebDriverWait(driver, 30).until(
          EC.presence_of_element_located((By.CLASS_NAME, "subFilterOver"))
      )
    html_data = driver.page_source
    soup_game_page = BeautifulSoup(html_data, 'lxml')
    section = soup_game_page.find('div', class_="container__detailInner").find('div', class_="section")
    game['stats']['full_time'] = get_stats(section)
    # Gett ESTADISTICAS - 1er TIEMPO
    driver.find_element(By.XPATH, '//a[@href="#/resumen-del-partido/estadisticas-del-partido/1"]').click()
    time.sleep(2)
    html_data = driver.page_source
    soup_game_page = BeautifulSoup(html_data, 'lxml')
    section = soup_game_page.find('div', class_="container__detailInner").find('div', class_="section")
    game['stats']['first_half'] = get_stats(section)
    # Get ESTADISTICAS - 2do TIEMPO
    driver.find_element(By.XPATH, '//a[@href="#/resumen-del-partido/estadisticas-del-partido/2"]').click()
    time.sleep(2)
    html_data = driver.page_source
    soup_game_page = BeautifulSoup(html_data, 'lxml')
    section = soup_game_page.find('div', class_="container__detailInner").find('div', class_="section")
    game['stats']['second_half'] = get_stats(section)
    # Get ALINEACIONES
    print('Collecting LINEUPs...')
    driver.find_element(By.XPATH, '//a[@href="#/resumen-del-partido/alineaciones"]').click()
    WebDriverWait(driver, 15).until(
          EC.presence_of_element_located((By.CLASS_NAME, "lf__lineUp"))
      )
    html_data = driver.page_source
    soup_game_page = BeautifulSoup(html_data, 'lxml')
    line_up_div = soup_game_page.find('div', class_="lf__lineUp")
    game['line_up'] = {
      'away': [],
      'home': []  
    }
    for item in line_up_div.find_all('div', class_="section"):
      if len(item.find_all('div', class_="section__title--center")) > 0:
        player_type = item.find('div', class_="section__title--center").text
        if player_type in ['Alineaciones iniciales', 'Suplentes', 'Jugadores ausentes', 'Entrenadores']:
          sides_div = item.find('div', class_="lf__sides")
          home_players = sides_div.find_all('div', class_="lf__side")[0]
          away_players = sides_div.find_all('div', class_="lf__side")[1]
          for player in home_players.find_all('div', class_="lf__participantNew"):
            # Collect Home
            if len(player.find_all('span', class_="_number_1gpx3_52")) > 0:
              number = player.find('span', class_="_number_1gpx3_52").text
            else:
              number = ''
            game['line_up']['home'].append({
              'type': player_type,
              'number': number,
              'player':   player.find('a', class_="_nameWrapper_1gpx3_35").find('strong', class_="_name_1gpx3_35").text,
              'player_link': 'https://www.flashscore.com.mx'+player.find('a', class_="_nameWrapper_1gpx3_35")['href']
            })
          for player in away_players.find_all('div', class_="lf__participantNew"):
            # Collect Away
            if len(player.find_all('span', class_="_number_1gpx3_52")) > 0:
              number = player.find('span', class_="_number_1gpx3_52").text
            else:
              number = ''
            game['line_up']['away'].append({
              'type': player_type,
              'number': number,
              'player':   player.find('a', class_="_nameWrapper_1gpx3_35").find('strong', class_="_name_1gpx3_35").text,
              'player_link': 'https://www.flashscore.com.mx'+player.find('a', class_="_nameWrapper_1gpx3_35")['href']
            })
    # Get COMENTARIOS
    print('Collecting COMMENTS...')
    game['comments'] = get_comments(driver)
    # Add Player Personal Data to Lineup
    print('Collecting players personal data...') 
    for player in game['line_up']['away']:
      player = get_player_data(player)
    for player in game['line_up']['home']:
      player = get_player_data(player)
    # break
  # Write to Excel
  print("Writing to Excel...")
  writer = excel.excelwriter()
  for match in list_games_round9:
    print(f"Writing {match['id']}")
    # print(match)
    writer.create_ws(match['id'])
    writer.fill_general_details(match)
    row = writer.fill_summary(match['summary'])
    row = writer.fill_stats(match['stats'], row)
    row = writer.fill_lineup(match['line_up'], row)
    writer.fill_comments(match['comments'], row)
  writer.workbook.close()
print('Finished')
  

