import numpy, math
import pandas

config = {
    ### Player data
    "players_data.csv": r"C:\Users\ADMIN\OneDrive\Desktop\project_Data_Science\raw_data\player_data\players_data.csv",
    "players_stats.csv": r"C:\Users\ADMIN\OneDrive\Desktop\project_Data_Science\raw_data\player_data\players_stats.csv",
    
    ### Club data
    "club_players.csv": r"C:\Users\ADMIN\OneDrive\Desktop\project_Data_Science\raw_data\club_data\club_players.csv",
    "club.csv": r"C:\Users\ADMIN\OneDrive\Desktop\project_Data_Science\raw_data\club_data\club.csv",
    "league_goals.csv": r"C:\Users\ADMIN\OneDrive\Desktop\project_Data_Science\raw_data\club_data\league_goals.csv",
}

### Một số các hàm lẻ
def clean_minutes_played(value):
    if pandas.isna(value) or value == '-' or value == 0:
        return 0
    return int(value.replace("'", "").replace(".", ""))

def convert_money_str_to_float(value):
    """
    Hàm này chỉ hoạt động cho pandas.Series
    Hàm này nhận tham số là giá trị value dương (không có dấu trừ/cộng đằng trước)
    """
    if pandas.isna(value):
        return numpy.nan
    if value == "0" or value == "-":
        return numpy.nan
    d = {
        "bn": 1e9,
        "m": 1e6,
        "k": 1e3
    }
    if value[-2:] == "bn":
        s = float(value[1: len(value)-2])*d["bn"]
    else:
        s = float(value[1: len(value)-1])*d[value[-1]]
    return s

def convert_negative_postive_money_str_to_float(value):
    """
    Hàm này chỉ hoạt động cho pandas.Series
    Hàm này nhận tham số là giá trị value có dấu trừ/cộng đằng trước.
    value dương có dấu cộng đứng đầu -> dấu euro -> số -> đơn vị
    value âm có dấu euro đứng đầu -> dấu trừ -> số -> đơn vị
    """
    d = {
        "m": 1e6,
        "k": 1e3
    }
    try:
        if value[0] == "+":
            return float(value[2: len(value)-1])*d[value[-1]]

        return -1*float(value[2: len(value)-1])*d[value[-1]]
    except:
        return numpy.nan

def convert_and_drop_na(players_data_df: pandas.DataFrame, players_stats_df: pandas.DataFrame, club_players_df: pandas.DataFrame, club_df: pandas.DataFrame, league_goals_df: pandas.DataFrame):
    ### Convert từ string euro -> float
    club_players_df["Player_MarketValue"] = club_players_df["Player_MarketValue"].map(convert_money_str_to_float)
    for field in ["avgMarketValue", "totalMarketValue", "Club_income", "Club_expenditure"]:
        club_df[field] = club_df[field].map(convert_money_str_to_float)
    club_df["Club_OverallBalance"] = club_df["Club_OverallBalance"].map(convert_negative_postive_money_str_to_float)

    ### Drop giá trị NaN
    # 1. players_data.csv
    players_data_df = players_data_df.drop(["shirt_number", "full_name", "given_name", "date_of_last_contract", "outfitter",
                                            "place_of_birth", "caps", "other_positions", "contract_expires", "agent", "contract_Joined"], 
                                            axis= 1)
    mode_foot = players_data_df["foot"].mode()[0]
    mean_height = players_data_df["height"].mean()
    players_data_df = players_data_df.fillna(value={"foot": mode_foot, "height": mean_height})
    mean_goals = players_data_df["goals"].mean()
    players_data_df = players_data_df.fillna(value= {"goals": math.ceil(mean_goals)})
    players_data_df.info()

    # 2. players_stats.csv
    players_stats_df = players_stats_df.fillna(value={
        "appearances": 0,
        "goals": 0,
        "asists": 0,
        "yellow_cards": 0,
        "second_yellow_cards": 0,
        "red_cards": 0,
        "minutes_played": 0,
        "goals_conceded": 0,
        "clean_sheets": 0
    })

    # 3. club_players.csv
    club_players_df = club_players_df.dropna()
    print("-"*10)
    club_players_df.info()
    print("-"*10)

    # 4. club.csv
    club_df = club_df.dropna(subset= ["Club_income", "Club_expenditure"])
    print("-"*10)
    club_df.info()
    print("-"*10)

    # 5. league_goals.csv
    # không có NaN

    return players_data_df, players_stats_df, club_players_df, club_df, league_goals_df

def run():
    players_data_df = pandas.read_csv(config["players_data.csv"])
    players_stats_df = pandas.read_csv(config["players_stats.csv"])
    club_players_df = pandas.read_csv(config["club_players.csv"])
    club_df = pandas.read_csv(config["club.csv"])
    league_goals_df = pandas.read_csv(config["league_goals.csv"]) 
   
    ### Đổi đơn vị và drop NaN
    players_data_df, players_stats_df, club_players_df, club_df, league_goals_df = convert_and_drop_na(players_data_df, players_stats_df, club_players_df, club_df, league_goals_df)
    
    ### Đổi tên 2 cột goals cho players_data và players_stats
    players_data_df = players_data_df.rename(columns= {"goals": "cumulative_goals"})
    players_stats_df = players_stats_df.rename(columns= {"goals": "2021_goals"}) 

    # Apply the modified function to the minutes_played column
    players_stats_df['minutes_played'] = players_stats_df['minutes_played'].apply(clean_minutes_played)
    # Extract age, remove birthday
    # Extract age from the date_of_birth column
    players_data_df['age'] = players_data_df['date_of_birth'].str.extract(r'\((\d+)\)').astype(float)
    # Then drop date_of_birth column
    players_data_df.drop(columns= ["date_of_birth"], inplace= True)

    # Perform an inner join
    merged_data = pandas.merge(players_data_df, players_stats_df, left_on='player_id', right_on= 'id', how= 'inner')    
    # drop tiếp các cột
    merged_data.drop(columns= ["name", "players_link", "id"], inplace= True)

    club_shortlist = club_df[["Club", "League", "avgAge", "avgMarketValue", "totalMarketValue", "Club_income", "Rank"]]
    columns_list = ["Club", "Country", "League", "avgAge", "avgMarketValue", "totalMarketValue", "Club_income", "Rank"]
    dict_name = {}
    for i in range(len(columns_list)) :
        dict_name[columns_list[i]] = "club_" + columns_list[i]
    print(dict_name)
    club_shortlist = club_shortlist.rename(columns= dict_name)

    # Perform an inner join
    full_data = pandas.merge(merged_data, club_shortlist, left_on='current_club', right_on= "club_Club", how= "left")
    full_data = full_data.rename(columns= {"club_Club" : "club"})

    return players_data_df, players_stats_df, club_players_df, club_df, league_goals_df, full_data

# run()
