import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import './GameComponent.css'

// Enums (as you defined)
enum PitchingStyle {
    Fastballs = "Fastballs",
    BreakingBalls = "Breaking Balls",
    Changeups = "Changeups"
}

enum HittingStyle {
    Power = "Power Hitter",
    Switch = "Switch Hitter",
    Designated = "Designated Hitter"
}

// Type Definitions
interface GameState {
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

interface CommentaryEntry {
    commentary: string;
    audio_url?: string;
    timestamp: string;
    action_type?: string;
}

interface GameResponse {
    game_state: GameState;
    commentary?: string;
    audio_url?: string;
}

interface CommentaryHistory {
    text_commentaries: string[];
    audio_urls: string[];
}

const baseUrl = "http://localhost:8000/api/v1";

const GameComponent: React.FC = () => {

    // Add navigation hook
    const navigate = useNavigate();
    
    // Hooks and state
    const { gameId } = useParams<{ gameId: string }>();
    const { user, token } = useAuth();

    // State management
    const [gameState, setGameState] = useState<GameState | null>(null);
    const [commentaries, setCommentaries] = useState<CommentaryEntry[]>([]);
    const [currentAudioIndex, setCurrentAudioIndex] = useState<number | null>(null);

    // Audio reference and state
    const audioRef = useRef<HTMLAudioElement>(null);
    const [isAudioPlaying, setIsAudioPlaying] = useState(false);

    // Fetch game state and commentaries
    const fetchGameData = useCallback(async () => {
        try {
            const gameResponse = await axios.get(`${baseUrl}/games/${gameId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
    
            setGameState(gameResponse.data.state);
    
            // Fetch commentary separately
            const commentaryResponse = await axios.get(`${baseUrl}/games/${gameId}/commentary`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            // Handle commentary from dedicated endpoint
            if (commentaryResponse.data.commentaries && commentaryResponse.data.audio_commentaries) {
                const mergedCommentaries = commentaryResponse.data.commentaries.map((commentary, index) => ({
                    commentary,
                    audio_url: commentaryResponse.data.audio_commentaries[index] || undefined
                }));

                setCommentaries(mergedCommentaries);
            }
        } catch (error) {
            console.error('Error fetching game data:', error);
        }
    }, [gameId, token]);

    // Determine if current user can perform action
    const canPerformAction = useCallback(() => {
        if (!gameState || !user) return false;

        // Top of inning: Team1 bats
        if (gameState.is_top_inning) {
            return user.uid === gameState.team1.user_id;
        }

        // Bottom of inning: Team2 bats
        return user.uid === gameState.team2.user_id;
    }, [gameState, user]);

    // Pitch action
    const performPitch = useCallback(async () => {
        try {
            const response = await axios.post<GameResponse>(
                `${baseUrl}/games/${gameId}/pitch`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    params: {
                        pitch_style: PitchingStyle.Fastballs
                    },
                }
            );

            // Update game state
            setGameState(response.data.game_state);

            // Add new commentary
            if (response.data.commentary) {
                const newCommentary: CommentaryEntry = {
                    commentary: response.data.commentary,
                    audio_url: response.data.audio_url,
                    timestamp: new Date().toISOString(),
                    action_type: 'pitch'
                };

                setCommentaries(prev => [...prev, newCommentary]);

                // Automatically play audio if available
                if (response.data.audio_url) {
                    playAudioCommentary(newCommentary);
                }
            }
        } catch (error) {
            console.error('Error performing pitch:', error);
        }
    }, [gameId, token]);

    // Bat action
    const performBat = useCallback(async () => {
        try {
            const response = await axios.post<GameResponse>(
                `${baseUrl}/games/${gameId}/bat`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    params: {
                        hit_style: HittingStyle.Power
                    },
                }
            );

            // Update game state
            setGameState(response.data.game_state);

            // Add new commentary
            if (response.data.commentary) {
                const newCommentary: CommentaryEntry = {
                    commentary: response.data.commentary,
                    audio_url: response.data.audio_url,
                    timestamp: new Date().toISOString(),
                    action_type: 'bat'
                };

                setCommentaries(prev => [...prev, newCommentary]);

                // Automatically play audio if available
                if (response.data.audio_url) {
                    playAudioCommentary(newCommentary);
                }
            }
        } catch (error) {
            console.error('Error performing bat:', error);
        }
    }, [gameId, token]);

    // Audio commentary playback
    const playAudioCommentary = useCallback((commentary: CommentaryEntry) => {
        if (audioRef.current && commentary.audio_url) {
            // Stop current audio if playing
            if (isAudioPlaying) {
                audioRef.current.pause();
            }

            // Set new audio source
            audioRef.current.src = commentary.audio_url;
            audioRef.current.play()
                .then(() => setIsAudioPlaying(true))
                .catch(error => console.error('Audio play error:', error));

            // Find and set current commentary index
            const index = commentaries.findIndex(
                c => c.audio_url === commentary.audio_url
            );
            setCurrentAudioIndex(index);
        }
    }, [commentaries, isAudioPlaying]);

    // Forfeit game function
    const forfeitGame = useCallback(async () => {
        try {
            // Confirm forfeit action
            const confirmForfeit = window.confirm(
                "Are you sure you want to forfeit the game? This action cannot be undone."
            );

            if (!confirmForfeit) return;

            const response = await axios.post(
                `${baseUrl}/games/${gameId}/forfeit`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            // Show forfeit result
            alert(`Game forfeited. ${response.data.winner ? 'Opponent wins!' : 'Game ended.'}`);

            // Redirect to a suitable page after forfeit
            navigate('/matchmaking'); // or wherever you want to redirect
        } catch (error) {
            console.error('Error forfeiting game:', error);
            
            // Handle specific error scenarios
            if (axios.isAxiosError(error)) {
                alert(error.response?.data?.detail || 'Failed to forfeit game');
            } else {
                alert('An unexpected error occurred');
            }
        }
    }, [gameId, token, navigate]);

    // Audio event listeners
    useEffect(() => {
        const audioElement = audioRef.current;

        const handleAudioEnded = () => {
            setIsAudioPlaying(false);
            setCurrentAudioIndex(null);
        };

        if (audioElement) {
            audioElement.addEventListener('ended', handleAudioEnded);
            return () => {
                audioElement.removeEventListener('ended', handleAudioEnded);
            };
        }
    }, []);

    // Fetch initial game data
    useEffect(() => {
        fetchGameData();
    }, [fetchGameData]);

    // Render game actions based on current inning and user
    const renderGameActions = () => {
        if (!gameState) return null;

        // Top of inning: Team1 bats, Team2 pitches
        if (gameState.is_top_inning) {
            return (
                <div className="game-actions">
                    {canPerformAction() ? (
                        <button
                            onClick={performBat}
                            className="bat-button"
                        >
                            Bat (Team 1)
                        </button>
                    ) : (
                        <button
                            onClick={performPitch}
                            className="pitch-button"
                        >
                            Pitch (Team 2)
                        </button>
                    )}
                </div>
            );
        }

        // Bottom of inning: Team2 bats, Team1 pitches
        return (
            <div className="game-actions">
                {canPerformAction() ? (
                    <button
                        onClick={performBat}
                        className="bat-button"
                    >
                        Bat (Team 2)
                    </button>
                ) : (
                    <button
                        onClick={performPitch}
                        className="pitch-button"
                    >
                        Pitch (Team 1)
                    </button>
                )}
            </div>
        );
    };

    // Toggle audio playback
    const toggleAudioPlayback = useCallback((commentary: CommentaryEntry) => {
        if (audioRef.current) {
            if (isAudioPlaying && currentAudioIndex !== null) {
                // If currently playing, pause
                audioRef.current.pause();
                setIsAudioPlaying(false);
            } else {
                // If not playing or different audio, play
                playAudioCommentary(commentary);
            }
        }
    }, [isAudioPlaying, currentAudioIndex, playAudioCommentary]);

    return (
        <div className="game-container">

            {/* Forfeit Game Section */}
            {gameState && canPerformAction() && (
                <div className="forfeit-section">
                    <button 
                        className="forfeit-button"
                        onClick={forfeitGame}
                    >
                        Forfeit Game
                    </button>
                </div>
            )}
            
            {/* Hidden audio element */}
            <audio ref={audioRef} />

            {/* Game State Display */}
            {gameState && (
                <div className="game-state">
                    <h2>Game State</h2>
                    <p>Inning: {gameState.inning} {gameState.is_top_inning ? 'Top' : 'Bottom'}</p>
                    <p>Outs: {gameState.outs}</p>
                    <p>Team 1 Score: {gameState.team1.score}</p>
                    <p>Team 2 Score: {gameState.team2.score}</p>
                </div>
            )}

            {/* Dynamic Game Actions */}
            {renderGameActions()}

            {/* Commentary Display */}
            <div className="commentary-section">
                <h2>Game Commentary</h2>
                {commentaries.map((entry, index) => (
                    <div
                        key={index}
                        className={`commentary-entry ${index === currentAudioIndex ? 'active' : ''}`}
                    >
                        <p>{entry.commentary}</p>
                        {entry.audio_url && (
                            <button
                                onClick={() => toggleAudioPlayback(entry)}
                            >
                                {isAudioPlaying && currentAudioIndex === index
                                    ? 'Pause'
                                    : 'Play Audio'}
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default GameComponent;