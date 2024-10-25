import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import ListGroup from "react-bootstrap/ListGroup";
import { GiSpiderBot } from "react-icons/gi";
import { MdManageHistory } from "react-icons/md";
import { FaArrowUp } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import { IoSettingsOutline } from "react-icons/io5";

const ApiFrontend = () => {
  const navi = useNavigate();
  // const backend_url =  "http://52.168.150.249:8000"
  // const backend_url =  "http://0.0.0.0:8000"
  // var backend_url = "http://127.0.0.1:8000";
  const backend_url =  "http://4.186.63.222:8000"



  const [message, setMessage] = useState("");
  const [responseHistory, setResponseHistory] = useState([]);
  const [loader, setLoader] = useState(false);
  const [error, setError] = useState(null);
  const [chats, setChats] = useState([]);
  const [sessionSetID, setSessionID] = useState(null);
  const chatContainerRef = useRef(null);

  // eslint-disable-next-line no-self-compare
  const [currentResponse, setCurrentResponse] = useState(undefined);

  const generateUniqueId = () =>
    Date.now() + Math.random().toString(36).substr(2, 9);

  const addNewChat = useCallback(() => {
    const uniqueID = generateUniqueId();
    setSessionID(uniqueID);
    setResponseHistory([]);
  }, []);

  const handleSessionId = async (sessionID) => {
    const url = `${backend_url}/api/session`;
    const body = { sessionID: sessionID.session_id };

    try {
      const result = await axios.post(url, body);
      if (result.data) {
        setResponseHistory(result.data);
        setError(null); // Clear any previous errors
      } else {
        setError("No response from the API");
      }
    } catch (error) {
      setError(`Error fetching session data: ${error.message}`);
    }
  };

  const fetchSession = async () => {
    const url = `${backend_url}/api/session`;
    const body = { sessionID: "" }; // Adjust this if your API requires a session ID

    try {
      const result = await axios.post(url, body);
      if (result.data) {
        return result.data;
      }
    } catch (error) {
      console.error("Error fetching session:", error);
    }
    return [];
  };

  useEffect(() => {
    const fetchData = async () => {
      const response = await fetchSession();
      setChats(response);
      addNewChat();
    };
    fetchData();
  }, [addNewChat]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [responseHistory]);

  const handleSend = async () => {
    if (!message.trim()) {
      setError("Please enter a message.");
      return;
    }

    const apiUrl = `${backend_url}/llm_response/${message}`;
    const singleEntry =
      responseHistory.length > 0 ? responseHistory[0].session_id : sessionSetID;

    setLoader(true);
    try {
      const body = { sessionID: singleEntry };
      const response = await axios.post(apiUrl, body, {
        responseType: "stream",
        adapter: "fetch",
      });
      setLoader(false);

      // Read the stream response
      const reader = response.data.getReader();
      const decoder = new TextDecoder();
      let dataLine = "";

      // Add a new entry for the current message in response history
      setResponseHistory((prevResponses) => [
        ...prevResponses,
        { session_id: singleEntry, human_query: message, ai_response: "" },
      ]);

      let currentIndex = responseHistory.length; // Index of the latest response

      let partialWord = ""; // To handle word breaks between chunks

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
      
        const chunk = decoder.decode(value, { stream: true });
      
        // Combine any partial word from the last chunk with the new chunk
        const combinedChunk = partialWord + chunk;
      
        // Clean up the chunk and remove unnecessary spaces
        const cleanedChunk = combinedChunk.replace(/\s+/g, " ").trim();
      
        // Find if there's a partial word at the end of the cleaned chunk
        const words = cleanedChunk.split(" ");
        partialWord = words.pop(); // Save the last word as a partial word for the next chunk
      
        // Rebuild the dataLine without the partial word
        dataLine += (dataLine ? " " : "") + words.join(" ");
      
        // Update the most recent response with the latest streamed data
        setResponseHistory((prevResponses) => {
          const updatedResponses = [...prevResponses];
          updatedResponses[currentIndex].ai_response = dataLine; // Update the response text in the same line
          return updatedResponses;
        });
      }
      
      // After the loop, add the remaining partial word to the dataLine
      if (partialWord) {
        dataLine += (dataLine ? " " : "") + partialWord;
        setResponseHistory((prevResponses) => {
          const updatedResponses = [...prevResponses];
          updatedResponses[currentIndex].ai_response = dataLine;
          return updatedResponses;
        });
      }
      
     
    } catch (e) {
      setLoader(false);
      setError(`Error: ${e.message}`);
    }

    setMessage("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const formatResponse = (text) => {
    if (!text) return text;

    // Replace headings, lists, and important text with HTML tags
    return text
    .replace(/### (.+)/g, "<strong>$1</strong>") // Bold for section titles
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>") // Bold for important text
    .replace(/(?:\d+\.)/g, "<br><strong>$&</strong>") // Add new line and bold for numbered points
    .replace(/- (.+)/g, "<li>$1</li>") // Convert list items
    .replace(/\n/g, "<br>") // Replace new lines with breaks
    .replace(/([.!?])\s+/g, "$1<br><br>") // Add double breaks after sentences
    .replace(/<li>(.*?)<\/li>/g, "<li>$1</li>") // Ensure list items are well-formed
    .replace(/(<br>)+/g, "<br>"); // Remove extra line breaks// Remove extra line breaks
};


  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-2">
          <div
            className="d-flex flex-column bg-light h-100"
            style={{
              position: "fixed",
              width: "16%",
              height: "100vh",
              borderRight: "1px solid #ddd",
            }}
          >
            <div className="p-3 border-bottom">
              <h4 className="mb-0 d-flex align-items-center justify-content-between">
                History <MdManageHistory size={25} />
              </h4>
            </div>

            <div className="p-3 border-bottom">
              <button
                className="btn btn-primary w-100 d-flex align-items-center justify-content-center"
                onClick={addNewChat}
              >
                New Chat
              </button>
            </div>

            <div
              className="flex-grow-1 overflow-auto p-3"
              style={{ maxHeight: "calc(100vh - 150px)" }}
            >
              <ListGroup variant="flush">
                {chats.length > 0 ? (
                  chats.map((chat, index) => (
                    <ListGroup.Item
                      key={chat.session_id}
                      action
                      onClick={() => handleSessionId(chat)}
                      className="mb-2"
                      style={{
                        cursor: "pointer",
                        borderRadius: "5px",
                        border: "1px solid #ddd",
                        padding: "10px 15px",
                        transition: "background-color 0.2s",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.backgroundColor = "#f1f1f1")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.backgroundColor = "transparent")
                      }
                    >
                      {chat.session_name || `Session ${index + 1}`}
                    </ListGroup.Item>
                  ))
                ) : (
                  <ListGroup.Item>No history available</ListGroup.Item>
                )}
                {currentResponse && (
                  <ListGroup.Item
                    key={currentResponse.session_id}
                    action
                    onClick={() => handleSessionId(currentResponse)}
                    className="mb-2"
                    style={{
                      cursor: "pointer",
                      borderRadius: "5px",
                      border: "1px solid #ddd",
                      padding: "10px 15px",
                      transition: "background-color 0.2s",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.backgroundColor = "#f1f1f1")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.backgroundColor = "transparent")
                    }
                  >
                    {currentResponse.session_name || `Session current ${1}`}
                  </ListGroup.Item>
                )}
              </ListGroup>
            </div>

            <div className="p-3 border-top d-flex justify-content-center">
              <IoSettingsOutline
                onClick={() => navi("/page/integration")}
                size={32}
                style={{ cursor: "pointer" }}
              />
            </div>
          </div>
        </div>

        <div
          className="col-10 main-chat-container"
          style={{ backgroundColor: "#b8babe" }}
        >
          <div
            style={{
              height: "100vh",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div className="card-header" />
            <div
              className="card-body"
              ref={chatContainerRef}
              style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                overflowY: "auto",
              }}
            >
              <div
                className="chat-container mt-4"
                style={{ flexGrow: 1, paddingLeft: "150px" }}
              >
                {loader ? (
                  <div
                    className="d-flex justify-content-center align-items-center"
                    style={{ height: "80vh" }}
                  >
                    <div className="spinner-border" role="status"></div>
                  </div>
                ) : (
                  <div className="container_show_response">
                    {responseHistory.length > 0 &&
                      responseHistory.map((res, index) => (
                        <div key={index} className="chat-message-container">
                          <div className="chat-bubble chat-bubble-user">
                            <p>{res.human_query}</p>
                          </div>
                          <div className="chat-bubble chat-bubble-ai">
                            <p
                              dangerouslySetInnerHTML={{
                                __html: formatResponse(res.ai_response),
                              }}
                            />
                              
                          {/* <p> {res?.ai_response}</p> */}
                          </div>
                        </div>
                      ))}
                    {error && (
                      <div className="chat-bubble chat-bubble-error">
                        <p>{error}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="card-footer">
              <div
                className="form-group d-flex align-items-center input_container"
                style={{ padding: "10px" }}
              >
                <input
                  type="text"
                  id="message"
                  className="form-control input_query"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter your message..."
                />
                <button
                  className="btn btn-primary btn-sm button_handleSend"
                  onClick={handleSend}
                >
                  <FaArrowUp />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiFrontend;
