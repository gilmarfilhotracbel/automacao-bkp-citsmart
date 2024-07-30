import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import { Button, Container, Typography, Box, CircularProgress, Paper, IconButton, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from '@mui/material';
import { styled } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';
import CheckIcon from '@mui/icons-material/Check';
import logoTracbel from './logotracbel.png';
import logoCITSmart from './citsmart.png';

const UploadButton = styled(Button)(({ theme }) => ({
  backgroundColor: '#FFBD59',
  '&:hover': {
    backgroundColor: '#b2843e',
  },
}));

const RunButton = styled(Button)(({ theme }) => ({
  backgroundColor: '#a4cd39',
  '&:hover': {
    backgroundColor: '#4caf50',
  },
}));

const FileButton = styled(Button)(({ theme }) => ({
  backgroundColor: '#9e9e9e',
  '&:hover': {
    backgroundColor: '#757575',
  },
}));

const FileNameBox = styled(Box)(({ theme, success }) => ({
  backgroundColor: success ? '#c8e6c9' : '#eeeeee',
  padding: theme.spacing(1),
  borderRadius: theme.shape.borderRadius,
  marginTop: theme.spacing(1),
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
}));

const socket = io('http://localhost:5000');

function FileUploader() {
  const [selectedCSV, setSelectedCSV] = useState(null);
  const [selectedZIP, setSelectedZIP] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadFilesSuccess, setUploadFilesSuccess] = useState(false);
  const [openModal, setOpenModal] = useState(false);
  const [ticketNumbers, setTicketNumbers] = useState([]);

  useEffect(() => {
    socket.on('ticket_updated', (data) => {
      setTicketNumbers((prevTickets) => [...prevTickets, data.ticket_number]);
    });

    return () => {
      socket.off('ticket_updated');
    };
  }, []);

  const handleCSVChange = event => {
    setSelectedCSV(event.target.files[0]);
    setUploadStatus('');
    setUploadSuccess(false);
    setUploadFilesSuccess(false);
  };

  const handleZIPChange = event => {
    setSelectedZIP(event.target.files[0]);
    setUploadStatus('');
    setUploadSuccess(false);
    setUploadFilesSuccess(false);
  };

  const handleRemoveCSV = () => {
    setSelectedCSV(null);
  };

  const handleRemoveZIP = () => {
    setSelectedZIP(null);
  };

  const handleUpload = async () => {
    if (!selectedCSV || !selectedZIP) {
      setUploadStatus('Por favor, selecione ambos os arquivos para fazer o upload.');
      return;
    }

    const formData = new FormData();
    formData.append('csv', selectedCSV);
    formData.append('zip', selectedZIP);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData);
      setUploadStatus('Upload feito com sucesso!');
      setUploadSuccess(true);
      setUploadFilesSuccess(true);
      console.log(response.data);
    } catch (error) {
      console.error('Erro no upload:', error.response);
      setUploadStatus('Erro ao fazer upload dos arquivos.');
      setUploadSuccess(false);
      setUploadFilesSuccess(false);
    }
  };

  const handleButtonClick = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const result = await response.json();
      console.log(result);
      setLoading(false);
      setOpenModal(true);
    } catch (error) {
      console.error('Error:', error);
      setLoading(false);
    }
  };

  const handleCloseModal = async () => {
    const formData = new FormData();
    await axios.post('http://localhost:5000/close', formData);
    setOpenModal(false);
    setSelectedCSV(null);
    setSelectedZIP(null);
    setUploadSuccess(false);
    setUploadFilesSuccess(false);
    setUploadStatus('');
    setTicketNumbers([]); // Reset ticket numbers when closing
  };

  return (
    <Box sx={{ bgcolor: '#f5f5f5', minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column' }}>
      <Container maxWidth="sm">
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2, bgcolor: '#fafafa', boxShadow: 3 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Box sx={{ mb: 2 }}>
              <img src={logoCITSmart} alt="Logo CITSmart" style={{ maxWidth: '100%', height: 'auto' }} />
            </Box>
            <Typography variant="h4" gutterBottom>Backup</Typography>
            <input
              accept=".csv"
              style={{ display: 'none' }}
              id="csv-upload"
              type="file"
              onChange={handleCSVChange}
              disabled={uploadFilesSuccess}
            />
            <label htmlFor="csv-upload">
              <FileButton variant="contained" component="span" sx={{ m: 1 }} disabled={uploadFilesSuccess}>
                Upload CSV
              </FileButton>
            </label>
            <input
              accept=".zip"
              style={{ display: 'none' }}
              id="zip-upload"
              type="file"
              onChange={handleZIPChange}
              disabled={uploadFilesSuccess}
            />
            <label htmlFor="zip-upload">
              <FileButton variant="contained" component="span" sx={{ m: 1 }} disabled={uploadFilesSuccess}>
                Upload ZIP
              </FileButton>
            </label>
            <UploadButton variant="contained" onClick={handleUpload} sx={{ m: 1 }} disabled={uploadFilesSuccess}>
              Anexar
            </UploadButton>
            <Box sx={{ mt: 2 }}>
              <RunButton variant="contained" onClick={handleButtonClick} sx={{ m: 1 }} disabled={!uploadSuccess || loading}>
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Executar Backup'}
              </RunButton>
            </Box>
            <Typography variant="body1" color="textSecondary" sx={{ mt: 2 }}>
              {uploadStatus}
            </Typography>
            <Box sx={{ mt: 2 }}>
              {selectedCSV && (
                <FileNameBox success={uploadFilesSuccess}>
                  <Typography variant="body2" color="textSecondary">CSV: {selectedCSV.name}</Typography>
                  <IconButton size="small" disabled={uploadFilesSuccess} onClick={handleRemoveCSV}>
                    {uploadFilesSuccess ? <CheckIcon /> : <CloseIcon />}
                  </IconButton>
                </FileNameBox>
              )}
              {selectedZIP && (
                <FileNameBox success={uploadFilesSuccess}>
                  <Typography variant="body2" color="textSecondary">ZIP: {selectedZIP.name}</Typography>
                  <IconButton size="small" disabled={uploadFilesSuccess} onClick={handleRemoveZIP}>
                    {uploadFilesSuccess ? <CheckIcon /> : <CloseIcon />}
                  </IconButton>
                </FileNameBox>
              )}
            </Box>
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography variant="h6">Tickets Baixados:</Typography>
              <Box 
                sx={{ 
                  mt: 2, 
                  bgcolor: '#eeeeee', 
                  maxHeight: 200, 
                  overflowY: 'auto', 
                  p: 2, 
                  borderRadius: 2,
                  boxShadow: 1
                }}
              >
                {ticketNumbers.length > 0 ? (
                  ticketNumbers.map((ticket, index) => (
                    <Typography key={index} variant="body2">
                      Ticket {ticket}
                    </Typography>
                  ))
                ) : (
                  <Typography variant="body2" color="textSecondary">
                    Nenhum ticket baixado ainda.
                  </Typography>
                )}
              </Box>
            </Box>

          </Box>
        </Paper>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <img src={logoTracbel} alt="Logo Tracbel" style={{ maxWidth: '150px', height: 'auto' }} />
        </Box>
      </Container>
      <Dialog open={openModal} onClose={handleCloseModal}>
        <DialogTitle>Processo Concluído</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Processo concluído com sucesso!
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseModal} color="primary">
            Finalizar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default FileUploader;
