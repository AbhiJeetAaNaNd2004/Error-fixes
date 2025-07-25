import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import Input from '../components/UI/Input';
import Modal from '../components/UI/Modal';
import apiService from '../services/api';
import { handleApiError } from '../utils/helpers';

const DepartmentManagement = () => {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedDept, setSelectedDept] = useState(null);
  const [deptName, setDeptName] = useState('');

  const loadDepartments = useCallback(async () => {
    try {
      const data = await apiService.getDepartments();
      setDepartments(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDepartments();
  }, [loadDepartments]);

  const handleOpenModal = (dept = null) => {
    setIsEditing(!!dept);
    setSelectedDept(dept);
    setDeptName(dept ? dept.department_name : '');
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure?')) {
      try {
        await apiService.deleteDepartment(id);
        await loadDepartments();
      } catch (err) {
        setError(handleApiError(err));
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        await apiService.updateDepartment(selectedDept.id, deptName);
      } else {
        await apiService.createDepartment(deptName);
      }
      setShowModal(false);
      await loadDepartments();
    } catch (err) {
      setError(handleApiError(err));
    }
  };

  return (
    <Layout title="Department Management">
      <div className="flex justify-end mb-4">
        <Button onClick={() => handleOpenModal()}>Add Department</Button>
      </div>
      <Card>
        {loading ? <p>Loading...</p> : (
          <ul>
            {departments.map(dept => (
              <li key={dept.id} className="flex justify-between items-center p-2 border-b">
                <span>{dept.department_name}</span>
                <div>
                  <Button variant="outline" size="sm" onClick={() => handleOpenModal(dept)}>Edit</Button>
                  <Button variant="danger" size="sm" onClick={() => handleDelete(dept.id)}>Delete</Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={isEditing ? 'Edit Department' : 'Create Department'}>
        <form onSubmit={handleSubmit}>
          <Input label="Department Name" value={deptName} onChange={(e) => setDeptName(e.target.value)} required />
          <div className="mt-4 flex justify-end">
            <Button type="submit">Save</Button>
          </div>
        </form>
      </Modal>
    </Layout>
  );
};

export default DepartmentManagement;
