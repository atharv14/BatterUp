import pandas as pd
import json
from datetime import datetime

def csv_to_json_with_rename(csv_path, column_mapper, stat_type):
    """
    Convert baseball statistics CSV to JSON format with renamed columns as keys.
    """
    try:
        # Read CSV with semicolon separator and ensure empty values are handled
        df = pd.read_csv(csv_path, sep=',', na_values=[''], keep_default_na=True)
        
        # Rename columns using the mapper
        df = df.rename(columns=column_mapper)
        
        # Convert DataFrame to records
        # Fill NaN values with None for proper JSON serialization
        records = df.replace({pd.NA: None}).to_dict(orient='records')
        
        # Create a list of players with their stats
        formatted_records = []
        for record in records:
            # Create player object with column names as keys
            player_stats = {}
            for key, value in record.items():
                # Convert float values to integers if they're whole numbers
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                player_stats[key] = value
            formatted_records.append(player_stats)
        
        output_file = f"baseball_{stat_type}_stats.json"
        
        # Write to JSON file with proper formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_records, f, indent=2, ensure_ascii=False)
        
        print(f"Created {stat_type} stats JSON file: {output_file}")
        print(f"Total records: {len(formatted_records)}")
        
        # Print sample of first record
        if formatted_records:
            print("\nSample record structure:")
            sample = dict(list(formatted_records[0].items())[:5])  # First 5 items
            print(json.dumps(sample, indent=2))
            
    except Exception as e:
        print(f"Error processing {stat_type} stats: {str(e)}")

# Column mappers remain the same
fielding_column_mapper = {
    'Rk': 'Rank',
    'Name': 'Player Name',
    'Age': 'Age',
    'Tm': 'Team',
    'Lg': 'League',
    'G': 'Games Played',
    'GS': 'Games Started',
    'CG': 'Complete Game',
    'Inn': 'Innings Played in Field',
    'Ch': 'Defensive Chances',
    'PO': 'Putouts',
    'A': 'Assists',
    'E': 'Errors',
    'DP': 'Double Plays Turned',
    'Fld%': 'Fielding Percentage',
    'Rtot': 'Total Fielding Runs Above Average',
    'Rtot/yr': 'Total Fielding Runs Above Average per 1200 Innings',
    'Rdrs': 'Runs Saved Above Average',
    'Rdrs/yr': 'Runs Save Above Average per 1200 Innings',
    'Rgood': 'Good Plays/Misplayed Runs Above Average',
    'RF/9': 'Range Factor per 9 Innings',
    'RF/G': 'Range Factor per Game',
    'Pos Summary': 'Positions Played'
}

batting_column_mapper = {
    'Rk': 'Rank',
    'Player': 'Player Name',
    'Age': 'Age',
    'Team': 'Team',
    'Lg': 'League',
    'WAR': 'Wins Above Replacement Players',
    'G': 'Games Played',
    'PA': 'Plate Appearances',
    'AB': 'At Bats',
    'R': 'Runs Scored',
    'H': 'Hits',
    '2B': 'Doubles',
    '3B': 'Triples',
    'HR': 'Home Runs',
    'RBI': 'Runs Battled In',
    'SB': 'Stolen Bases',
    'CS': 'Caught Stealing',
    'BB': 'Bases on Balls/Walks',
    'SO': 'Strikeouts',
    'BA': 'Hits/At Bats',
    'OBP': '(H + BB + HBP) / (At Bats + BB + HBP + SF)',
    'SLG': 'Total Bases/At Bats',
    'OPS': 'On Base + Slugging Percentages',
    'OPS+': 'OPS+',
    'rOBA': 'rOBA',
    'Rbat+': 'Rbat+',
    'TB': 'Total Bases',
    'GIDP': 'Doubles Plays Grounded Into',
    'HBP': 'Times Hit By a Pitch',
    'SH': 'Sacrifice Hits',
    'SF': 'Sacrifice Flies',
    'IBB': 'Intentional Bases on Balls',
    'Pos': 'Positions Played',
    'Awards': 'Awards'
}

pitching_column_mapper = {
    'Rk': 'Rank',
    'Player': 'Player Name',
    'Age': 'Age',
    'Team': 'Team',
    'Lg': 'League',
    'WAR': 'Wins Above Replacement Players',
    'W': 'Wins',
    'L': 'Losses',
    'W-L%': 'Win-Loss Percentage',
    'ERA': '9*ER/IP',
    'G': 'Games Pitched',
    'GS': 'Games Started',
    'GF': 'Games Finished',
    'CG': 'Completed Games',
    'SHO': 'Shutouts',
    'SV': 'Saves',
    'IP': 'Innings Pitched',
    'H': 'Hits',
    'R': 'Runs',
    'ER': 'Earned Runs (ER)',
    'HR': 'Home Runs',
    'BB': 'Bases on Balls/Walks',
    'IBB': 'Intentional Bases on Balls',
    'SO': 'Strikeouts',
    'HBP': 'Times Hit By a Pitch',
    'BK': 'Balks',
    'WP': 'Wild Pitches',
    'BF': 'Batters Faced',
    'ERA+': 'ERA+',
    'FIP': 'Fielding Independent Pitching',
    'WHIP': '(BB + H)/IP',
    'H9': '9*H/IP',
    'HR9': '9*HR/IP',
    'BB9': '9*BB/IP',
    'SO9': '9*SO/IP',
    'SO/BB': 'SO/BB',
    'Awards': 'Awards'
}

if __name__ == "__main__":
    print("Converting batting statistics...")
    csv_to_json_with_rename('2024_batting.csv', batting_column_mapper, 'batting')
    
    print("\n" + "="*50 + "\n")
    
    print("Converting pitching statistics...")
    csv_to_json_with_rename('2024_pitching.csv', pitching_column_mapper, 'pitching')
    
    print("\n" + "="*50 + "\n")
    
    print("Converting fielding statistics...")
    csv_to_json_with_rename('2024_fielding.csv', fielding_column_mapper, 'fielding')