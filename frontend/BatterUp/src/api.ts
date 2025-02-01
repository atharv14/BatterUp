export const apiRequest = async (
    endpoint: string,
    method: string = "GET",
    body: any = null,
    token: string // Pass the token explicitly
  ) => {
    const API_BASE_URL = "http://localhost:8000/api/v1"; // Adjust as needed
  
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`, // Use passed token
    };
  
    const options: RequestInit = {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    };
  
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
      if (!response.ok) {
        throw new Error(`HTTP Error! Status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("API Request Error:", error);
      throw error;
    }
  };
  