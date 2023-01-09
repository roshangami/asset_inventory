import React, { useEffect, useState } from "react"
import './Dashboard.css';
import DataTable from "react-data-table-component";
import Card from "@material-ui/core/Card";
import SortIcon from "@material-ui/icons/ArrowDownward";
import Button from '@mui/material/Button';
import { Select, MenuItem, FormHelperText, FormControl, InputLabel } from '@material-ui/core';
import { columns, headers, column } from "./Columns";
import { CSVLink } from "react-csv";
import jsPDF from 'jspdf'
import 'jspdf-autotable'
import { useNavigate } from "react-router-dom";
import { DatePicker, Space } from 'antd';
import { BsFileEarmarkExcelFill, BsFileEarmarkPdfFill } from "react-icons/bs";
import { RiRefreshLine } from "react-icons/ri";

const { RangePicker } = DatePicker;

const UserData = () => {

  let navigate = useNavigate();
  const routeChange = () => {
    let path = `/`;
    navigate(path);
  }


  const [dynamodb, setdynamodb] = useState([])
  const [s3, setS3] = useState([])
  const [ec2, setEC2] = useState([])
  const [rds, setRDS] = useState([])
  const [combineData, setCombineData] = useState([])
  const [filteredData, setFilteredData] = useState([])
  const [loadingData, setLoadingData] = useState(true);
  const [selected, setSelected] = useState('');

  const getData = async () => {
    await Promise.all([
      fetch("/afourtech-apigateway-frontend?resource=dynamodb"),
      fetch("/afourtech-apigateway-frontend?resource=s3"),
      fetch("/afourtech-apigateway-frontend?resource=ec2"),
      fetch("/afourtech-apigateway-frontend?resource=rds"),
    ])
      .then(([resDynamodb, resS3, resEC2, resRDS]) =>
        Promise.all([resDynamodb.json(), resS3.json(), resEC2.json(), resRDS.json()])
      )
      .then(([Dynamodb, S3, EC2, RDS]) => {
        let dataDynamodb = Dynamodb.Items
        let dataS3 = S3.Items
        let dataEC2 = EC2.Items
        let dataRDS = RDS.Items
        setdynamodb(dataDynamodb)
        setS3(dataS3)
        setEC2(dataEC2)
        setRDS(dataRDS)
        setLoadingData(false)
        setCombineData(dataDynamodb.concat(dataS3, dataEC2, dataRDS))
        setFilteredData(dataDynamodb.concat(dataS3, dataEC2, dataRDS))
      })
  }

  useEffect(() => {
    getData()
  }, [])

  const csvReport = {
    data: combineData,
    headers: headers,
    filename: 'data.csv'
  };

  const exportPDF = () => {
    const doc = new jsPDF()
    doc.autoTable({
      columns: column.map(col => ({ ...col, dataKey: col.field })),
      body: combineData,
      columnStyles: {
        0: { cellWidth: 27 },
        1: { cellWidth: 26 },
        2: { cellWidth: 20 },
        3: { cellWidth: 20 },
        4: { cellWidth: 20 },
        5: { cellWidth: 20 },
        6: { cellWidth: 26 },
      }
    })

    doc.save('data.pdf')
  }


  const selectionChangeHandler = (event) => {
    setSelected(event.target.value);
  };

  const allServices = () => {
    setFilteredData(combineData)
  }

  const filterDynamodb = () => {
    let newData = combineData.filter(service => service.ResourceType === "Dynamo DB")
    setFilteredData(newData)
  }

  const filterS3 = () => {
    let newData = combineData.filter(service => service.ResourceType === "S3")
    setFilteredData(newData)
  }

  const filterEC2Instance = () => {
    let newData = combineData.filter(service => service.ResourceType === "EC2Instance")
    setFilteredData(newData)
  }

  const filterRDSInstance = () => {
    let newData = combineData.filter(service => service.ResourceType === "RDSInstance")
    setFilteredData(newData)
  }

  const dateRange = (date) => {
    let start = new Date(date[0].$d)
    let end = new Date(date[1].$d)
    start = new Date(start).getTime()
    end = new Date(end).getTime()
    let result = combineData.filter(d => {
      var date = new Date(d.CreationDate).getTime();
      return (start < date && date < end);
    });
    setFilteredData(result)
  }


  console.log(filteredData)


  return (
    <div>
      <Card>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          float: 'right',
          margin: '5px'
        }}>
          <Button variant="outlined" onClick={routeChange} >Logout</Button>
        </div>
        <div style={{
          display: 'flex',
          flexDirection: 'row',
          float: 'right',
          marginTop: '45px',
        }}>
          <Button title="Refresh" onClick={getData} ><RiRefreshLine size={25} /></Button>
          <CSVLink {...csvReport} title="Export as CSV" ><BsFileEarmarkExcelFill size={23} /></CSVLink>
          <Button title="Export as PDF" onClick={exportPDF}><BsFileEarmarkPdfFill size={23} /></Button>

        </div>

        <div>
          <Space direction="vertical" size={12} style={{
            display: 'flex',
            flexDirection: 'row',
            float: 'left',
            marginLeft: '10px',
            marginTop: '45px',
          }} >
            <RangePicker
              format="MMM Do, YYYY"
              onChange={dateRange}
            />
          </Space>
          <FormControl style={{
            marginLeft: '20px',
            marginTop: '30px',
          }}>
            <InputLabel>Services</InputLabel>
            <Select value={selected} onChange={selectionChangeHandler}>
              <MenuItem onClick={allServices} value={1}>All</MenuItem>
              <MenuItem onClick={filterS3} value={2}>S3</MenuItem>
              <MenuItem onClick={filterDynamodb} value={3}>Dynamo DB</MenuItem>
              <MenuItem onClick={filterEC2Instance} value={4}>EC2Instance</MenuItem>
              <MenuItem onClick={filterRDSInstance} value={5}>RDSInstance</MenuItem>
            </Select>
            <FormHelperText>Select a service</FormHelperText>
          </FormControl>
        </div>
        <DataTable
          striped
          columns={columns}
          data={filteredData}
          defaultSortFieldId={1}
          sortIcon={<SortIcon />}
          progressPending={loadingData}
          pagination
        />
      </Card>
    </div>


  );
}

export default UserData