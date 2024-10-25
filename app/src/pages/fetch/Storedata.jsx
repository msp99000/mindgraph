import React, { useState } from 'react';
import { Card, Button, Spinner, Alert } from 'react-bootstrap'; // Import Bootstrap components
import 'bootstrap/dist/css/bootstrap.min.css'; // Ensure Bootstrap CSS is imported
 

function StoreData() {
  // var backend_url="http://49.43.100.205:8000"
  // var backend_url = "http://127.0.0.1:8000";
  // const backend_url = "http://0.0.0.0:8000";
  const backend_url =  "http://4.186.63.222:8000"

  //  const backend_url =  "http://52.168.150.249:8000"
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleStoreVector = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch(`${backend_url}/api/slack/store-vector`, {
        method: 'POST',
      });

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError('Failed to store vector. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
      <Card className="store-card" style={{ width: '30rem', padding: '20px' }}>
        <Card.Body>
          <Card.Title className="text-center mb-4">Create Vector Store</Card.Title>

          <Button onClick={handleStoreVector} variant="primary" className="w-100" disabled={loading}>
            {loading ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />{' '}
                Storing Data...
              </>
            ) : (
              'Store Vector'
            )}
          </Button>

          {/* Show loading spinner if request is in progress */}
          {loading && (
            <div className="d-flex justify-content-center mt-3">
              <Spinner animation="border" role="status" />
            </div>
          )}

          {/* Display the API response */}
          {response && (
            <Alert variant="success" className="mt-3 fade show">
              <strong>Success!</strong> Response: {JSON.stringify(response)}
            </Alert>
          )}

          {/* Display an error if one occurs */}
          {error && (
            <Alert variant="danger" className="mt-3 fade show">
              <strong>Error:</strong> {error}
            </Alert>
          )}
        </Card.Body>
      </Card>
    </div>
  );
}

export default StoreData;
