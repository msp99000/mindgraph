import React, { useState, useEffect } from "react";
import Form from "react-bootstrap/Form";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import Spinner from "react-bootstrap/Spinner";

function FetchSlack() {
  // var backend_url="http://49.43.100.205:8000"
  // const backend_url = "http://0.0.0.0:8000"
  const backend_url =  "http://4.186.63.222:8000"

  // var backend_url = "http://127.0.0.1:8000";
  // const backend_url =  "http://52.168.150.249:8000";
  const [organizations, setOrganizations] = useState([]);
  const [channels, setChannels] = useState([]);
  const navi = useNavigate();

  const [selectedOrg, setSelectedOrg] = useState({ id: "", name: "" });
  const [selectedChannel, setSelectedChannel] = useState({ id: "", name: "" });
  const [oldestUnix, setOldestUnix] = useState("");
  const [latestUnix, setLatestUnix] = useState("");
  const [loading, setLoading] = useState(false);
  const [slack_file, setSlack_file] = useState("");
  const [success, setSuccess] = useState(false);

  const token = "xoxp-6314615578211-6317235574564-7496265822324-2a37972e284a8379a4fbaae31bf94eff";

  useEffect(() => {
    const fetchSlackData = async () => {
      const apiUrl = `${backend_url}/api/slack/combined-info`;
      try {
        const result = await axios.post(apiUrl, { token }, { headers: { "Content-Type": "application/json" } });
        setOrganizations([result?.data?.team_info?.team]);
        setChannels(result?.data?.channels_info?.channels);
      } catch (error) {
        console.error("Error fetching combined info:", error);
      }
    };

    fetchSlackData();
  }, [token]);

  const handleOrgChange = (e) => {
    const selectedOrgId = e.target.value;
    const selectedOrgName = organizations.find((org) => org.id === selectedOrgId)?.name;
    setSelectedOrg({ id: selectedOrgId, name: selectedOrgName });
    setSelectedChannel({ id: "", name: "" });
  };

  const handleChannelChange = (e) => {
    const selectedChannelId = e.target.value;
    const selectedChannelName = channels.find((channel) => channel.id === selectedChannelId)?.name;
    setSelectedChannel({ id: selectedChannelId, name: selectedChannelName });
  };

  const convertToUnix = (date) => Math.floor(new Date(date).getTime() / 1000);

  const handleSubmit = async () => {
    const payload = {
      organization_id: selectedOrg.id,
      channel_id: selectedChannel.id,
      organization_name: selectedOrg.name,
      channel_name: selectedChannel.name,
      token: token,
    };

    const oldestUnixValue = convertToUnix(oldestUnix);
    const latestUnixValue = convertToUnix(latestUnix);
    if (oldestUnixValue !== null) {
      payload.oldest_unix = oldestUnixValue;
    }
    if (latestUnixValue !== null) {
      payload.latest_unix = latestUnixValue;
    }

    try {
      setLoading(true);
      setSuccess(false);
      const response = await axios.post(`${backend_url}/api/slack/embedding-data`, payload);
      setSlack_file(response.data.success);
      if (response.data.success) {
        setSuccess(true);
      }
    } catch (error) {
      console.error("Error occurred:", error);
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const handleLogout = () => {
    localStorage.removeItem("username");
    localStorage.removeItem("loginTime");
    navi("/login");
  };

  return (
    <div className="container my-5">
      {loading ? (
        <div className="d-flex justify-content-center align-items-center" style={{ height: "100vh" }}>
          <Spinner animation="border" />
        </div>
      ) : (
        <>
          <Card className="shadow-sm">
            <Card.Body>
              <Card.Title className="text-center mb-4">Fetch Data from Slack</Card.Title>

              {/* Organization Selection */}
              <Form.Group className="mb-3">
                <Form.Label>Organization Name:</Form.Label>
                <Form.Select value={selectedOrg.id} onChange={handleOrgChange} className="form-control">
                  <option value="">Select Organization</option>
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>

              {/* Channel Selection */}
              <Form.Group className="mb-3">
                <Form.Label>Channel Name:</Form.Label>
                <Form.Select value={selectedChannel.id} onChange={handleChannelChange} className="form-control">
                  <option value="">Select Channel</option>
                  {channels &&
                    channels.map((channel) => {
                      if (channel.context_team_id === selectedOrg.id) {
                        return (
                          <option key={channel.id} value={channel.id}>
                            {channel.name}
                          </option>
                        );
                      }
                      return null;
                    })}
                </Form.Select>
              </Form.Group>

              {/* Oldest Unix Time Selection */}
              <Form.Group className="mb-3">
                <Form.Label>Oldest Unix Time:</Form.Label>
                <Form.Control type="datetime-local" value={oldestUnix} onChange={(e) => setOldestUnix(e.target.value)} />
              </Form.Group>

              {/* Latest Unix Time Selection */}
              <Form.Group className="mb-4">
                <Form.Label>Latest Unix Time:</Form.Label>
                <Form.Control type="datetime-local" value={latestUnix} onChange={(e) => setLatestUnix(e.target.value)} />
              </Form.Group>

              {/* Submit Button */}
              <div className="d-flex justify-content-center">
                <Button variant="primary" onClick={handleSubmit}>
                  Fetch Data
                </Button>
              </div>

              {/* Success message */}
              {success && (
                <div className="alert alert-success mt-3">
                  Data has been fetched successfully!{" "}
                  <Button onClick={() => navi("/StoreData")} variant="link">
                    Go to Next Step
                  </Button>
                </div>
              )}
            </Card.Body>
          </Card>

          {/* Logout Button */}
          <div className="d-flex justify-content-end mt-3">
            <Button variant="danger" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

export default FetchSlack;
