import moment from 'moment';
import './Dashboard.css'


export const columns = [
    {
        id: 1,
        name: "Account Number",
        selector: (row) => row.AccountNumber,
        sortable: true,
        reorder: true,
        width: "140px",
    },
    {
        id: 2,
        name: "Resource Name",
        selector: (row) => row.ResourceName,
        sortable: true,
        reorder: true,
        width: "250px",
        // style: {
        //     background: "orange",
        // }
    },
    {
        id: 3,
        name: "Resource Id",
        selector: (row) => row.ResourceId,
        sortable: true,
        reorder: true,
        width: "250px"
    },
    {
        id: 4,
        name: "Resource Type",
        selector: (row) => row.ResourceType,
        sortable: true,
        reorder: true,
        width: "130px",
    },
    {
        id: 5,
        name: "Creation Date",
        selector: (row) => moment(row.CreationDate).format('DD-MM-YYYY, h:mm:ss a'),
        sortable: true,
        type: 'date',
        reorder: true,
        width: "150px",
    },
    {
        id: 6,
        name: "CreatedBy",
        selector: (row) => row.CreatedBy,
        sortable: true,
        reorder: true,
        width: "120px"
    },
    {
        id: 7,
        name: "Region",
        selector: (row) => row.Region,
        sortable: true,
        reorder: true,
        width: "120px",
    },
    {
        id: 8,
        name: "PrivateIp Address",
        selector: (row) => row.PrivateIpAddress,
        sortable: true,
        reorder: true,
        width: "145px",
    },
    {
        id: 9,
        name: "Instance Type",
        selector: (row) => row.InstanceType,
        sortable: true,
        reorder: true,
        width: "125px"
    }
];


export const headers = [
    { label: "Account Number", key: "AccountNumber", type: "numeric" },
    { label: "CreationDate", key: "CreationDate" },
    { label: "Region", key: "Region" },
    { label: "ResourceName", key: "ResourceName" },
    { label: "PrivateIpAddress", key: "PrivateIpAddress" },
    { label: "CreatedBy", key: "CreatedBy" },
    { label: "ResourceId", key: "ResourceId" },
    { label: "ResourceType", key: "ResourceType" },
];

export const column = [
    { title: "Account Number", field: "AccountNumber", type: "numeric" },
    { title: "CreationDate", field: "CreationDate", type: "numeric" },
    { title: "Region", field: "Region" },
    { title: "ResourceName", field: "ResourceName" },
    { title: "PrivateIpAddress", field: "PrivateIpAddress" },
    { title: "CreatedBy", field: "CreatedBy" },
    { title: "ResourceId", field: "ResourceId" },
    { title: "ResourceType", field: "ResourceType" },
]
