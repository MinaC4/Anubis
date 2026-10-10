import React, {useState} from 'react';
import axios from 'axios';
import {useSnackbar} from 'notistack';

import makeStyles from '@mui/styles/makeStyles';
import Input from '@mui/material/Input';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';

import standardStatusHandler from '../../../utils/standardStatusHandler';
import standardErrorHandler from '../../../utils/standardErrorHandler';

import StandardLayout from '../../../components/shared/Layouts/StandardLayout';
import UserItem from '../../../components/core/UserItem/UserItem';
import ListHeader from '../../../components/shared/ListHeader/ListHeader';
import ListPagination from '../../../components/shared/ListPagination/ListPagination.jsx';
import SectionHeader from '../../../components/shared/SectionHeader/SectionHeader';
import Divider from '../../../components/shared/Divider/Divider';

const useStyles = makeStyles((theme) => ({
  paper: {
    flex: 1,
    padding: theme.spacing(1),
  },
  studentList: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  dataGridPaper: {
    height: 800,
  },
  dataGrid: {
    height: '100%',
    display: 'flex',
  },
  autocomplete: {
    paddingBottom: theme.spacing(1),
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
  },
  search: {
    width: '100%',
    backgroundColor: theme.palette.dark.blue['100'],
    border: `1px solid ${theme.palette.dark.blue['200']}`,
    padding: theme.spacing(2),
    borderRadius: theme.spacing(1),
    marginTop: theme.spacing(2),
  },
}));


export default function Users() {
  const classes = useStyles();
  const {enqueueSnackbar} = useSnackbar();
  const [students, setStudents] = useState([]);
  const [page, setPage] = useState(0);

  const [refresh, setRefresh] = useState(0);

  const [searchQuery, setSearchQuery] = useState(undefined);
  const [addOpen, setAddOpen] = useState(false);
  const [netid, setNetid] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');

  React.useEffect(() => {
    axios.get('/api/admin/students/list').then((response) => {
      const data = standardStatusHandler(response, enqueueSnackbar);
      if (data?.students) {
        for (const student of data.students) {
          student.search = student.name.toLowerCase() +
            student.netid.toLowerCase() +
            (student.github_username ?? '').toString() +
            student.id.toLowerCase();
        }

        const students = [];
        while (data.students.length) {
          students.push(data.students.splice(0, 10));
        }

        setStudents(students);
      } else {
        enqueueSnackbar('Unable to fetch students', {variant: 'error'});
      }
    }).catch((error) => {
      enqueueSnackbar(error.toString(), {variant: 'error'});
    });
  }, [refresh]);

  React.useEffect(() => {
    if (searchQuery === '' || searchQuery === undefined) {
      setRefresh(refresh + 1);
      return undefined;
    }
    const newStudents = students.flat(Infinity).filter((student) =>
      student.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      student.netid.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (!!student.github_username && student.github_username.toLowerCase().includes(searchQuery.toLowerCase())),
    );

    const paginatedStudents = [];

    while (newStudents.length) {
      paginatedStudents.push(newStudents.splice(0, 10));
    }
    setStudents(paginatedStudents);
    setPage(0);
  }, [searchQuery]);

  return (
    <StandardLayout>
      <SectionHeader isPage title={'Students'} />
      <Divider />
      <Button variant="contained" onClick={() => setAddOpen(true)}>Add Student</Button>
      <Dialog open={addOpen} onClose={() => setAddOpen(false)} aria-labelledby="add-local-student-title">
        <DialogTitle id="add-local-student-title">Add local student</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus margin="dense" label="NetID" value={netid}
            onChange={(event) => setNetid(event.target.value)} fullWidth
          />
          <TextField
            margin="dense" label="Name" value={name}
            onChange={(event) => setName(event.target.value)} fullWidth
          />
          <TextField
            margin="dense" label="Student password" type="password"
            helperText="At least 12 characters; the student uses this on the sign-in page."
            value={password} onChange={(event) => setPassword(event.target.value)} fullWidth
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>Cancel</Button>
          <Button variant="contained" disabled={!netid.trim() || !name.trim() || password.length < 12} onClick={() => {
            axios.post('/api/admin/students/create-local', {netid, name, password}).then((response) => {
              if (standardStatusHandler(response, enqueueSnackbar)) {
                setAddOpen(false);
                setNetid('');
                setName('');
                setPassword('');
                setSearchQuery('');
                setRefresh((value) => value + 1);
              }
            }).catch(standardErrorHandler(enqueueSnackbar));
          }}>Create</Button>
        </DialogActions>
      </Dialog>
      <Input
        placeholder={'Search Student By NetId, Name or Github Username'}
        value={searchQuery}
        onChange={(event) => setSearchQuery(event.target.value)}
        className={classes.search}
      >
      </Input>
      <ListHeader sections={['Name', 'Github Username', 'netid', 'View']} />
      {students[page]?.length > 0 && (
        <div className={classes.studentList}>
          {students[page].map((student, index) => (
            <UserItem
              key={`${student.netid}-${index}`}
              githubUsername={student.github_username}
              id={student.id}
              netid={student.netid}
              name={student.name}
            />
          ))}
        </div>
      )}
      {students.length === 0 && <p>No students found in this course.</p>}
      {students.length > 1 && (
        <ListPagination
          page={page}
          maxPage={students.length}
          setPage={(page) => setPage(page)}
          prevPage={() => setPage((page) => {
            if (page === 0) {
              return students.length - 1;
            }
            return page - 1;
          })}
          nextPage={() => setPage((page + 1) % students.length)}
        />
      )}
    </StandardLayout>
  );
}
