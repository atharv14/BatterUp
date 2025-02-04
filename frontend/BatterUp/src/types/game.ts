// Type definitions
export interface CommentaryEntry {
    commentary: string;
    audio_url?: string;
    timestamp: string;
    action_type?: string;
}

export interface GameState {
    game_id: string;
    inning: number;
    is_top_inning: boolean;
    outs: number;
    team1: {
        score: number;
        user_id: string;
    };
    team2: {
        score: number;
        user_id: string;
    };
}

export interface GameResponse {
    game_state: GameState;
    commentary?: string;
    audio_url?: string;
}