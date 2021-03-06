#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR, MultiStepLR
import numpy as np
# import matplotlib.pyplot as plt
from math import *
import time
torch.cuda.set_device(1)
torch.set_default_tensor_type('torch.DoubleTensor')


# In[ ]:


# activation function
def activation(x):
    return x * torch.sigmoid(x) 


# In[ ]:


# exact solution
def u_ex(x):     
    temp = 1.0
    for i in range(space_dimension):
        temp = temp * torch.sin(pi*x[:, i])
    u_temp = x[:, -1] * temp
    return u_temp.reshape([x.size()[0], 1])


# In[ ]:


def f(x):
    temp = 1.0
    for i in range(space_dimension):
        temp = temp * torch.sin(pi*x[:, i])
    f_temp = (1.0 + space_dimension * x[:, -1] * pi**2) * temp
    return f_temp.reshape([x.size()[0], 1])


# In[ ]:


# build ResNet with three blocks
class Net(nn.Module):
    def __init__(self,input_size,width,output_size):
        super(Net,self).__init__()
        self.layer_in = nn.Linear(input_size,width)
        self.layer_1 = nn.Linear(width,width)
        self.layer_2 = nn.Linear(width,width)
        self.layer_3 = nn.Linear(width,width)
        self.layer_4 = nn.Linear(width,width)
        self.layer_5 = nn.Linear(width,width)
        self.layer_6 = nn.Linear(width,width)
        self.layer_out = nn.Linear(width,output_size)
    def forward(self,x):
        output = self.layer_in(x) 
        output = output + activation(self.layer_2(activation(self.layer_1(output)))) # residual block 1
        output = output + activation(self.layer_4(activation(self.layer_3(output)))) # residual block 2
        output = output + activation(self.layer_6(activation(self.layer_5(output)))) # residual block 3
        output = self.layer_out(output)
        return output


# In[ ]:


time_dimension = 1
space_dimension = 10
d = space_dimension + time_dimension # dimension of input include time and space variables
input_size = d 
width_1 = 10
output_size_1 = 1 
data_size = 2000


# In[ ]:


CUDA = torch.cuda.is_available()
# print('CUDA is: ', CUDA)
if CUDA:
    net_1 = Net(input_size, width_1, output_size_1).cuda() # network for u on gpu
else:
    net_1 = Net(input_size, width_1, output_size_1) # network for u on cpu


# In[ ]:


def model_u(x):
    x_temp = (x[:,0:d-1]).cuda()
    D_x_0 = torch.prod(x_temp, axis = 1).reshape([x.size()[0], 1]) 
    D_x_1 = torch.prod(1.0 - x_temp, axis = 1).reshape([x.size()[0], 1]) 
    model_u_temp = D_x_0 * D_x_1 * (x[:, -1]).reshape([x.size()[0], 1]) * net_1(x)
    return model_u_temp.reshape([x.size()[0], 1])


# In[ ]:


def generate_sample(data_size_temp):
    sample_temp = torch.rand(data_size_temp, d)
    return sample_temp.cuda()


# In[ ]:


def relative_l2_error():
    data_size_temp = 500
    x = generate_sample(data_size_temp).cuda() 
    predict = model_u(x)
    exact = u_ex(x)
    value = torch.sqrt(torch.sum((predict - exact)**2))/torch.sqrt(torch.sum((exact)**2))
    return value


# In[ ]:


# Xavier normal initialization for weights:
#             mean = 0 std = gain * sqrt(2 / fan_in + fan_out)
# zero initialization for biases
def initialize_weights(self):
    for m in self.modules():
        if isinstance(m,nn.Linear):
            nn.init.xavier_normal_(m.weight.data)
            if m.bias is not None:
                m.bias.data.zero_()


# In[ ]:


initialize_weights(net_1)


# In[ ]:


def loss_function(x):
#     x = generate_sample(data_size).cuda()
#     x.requires_grad = True
    u_hat = model_u(x)
    grad_u_hat = torch.autograd.grad(outputs = u_hat, inputs = x, grad_outputs = torch.ones(u_hat.shape).cuda(), create_graph = True)
    laplace_u_hat = torch.zeros([len(grad_u_hat[0]), 1]).cuda()
    for index in range(space_dimension):
        p_temp = grad_u_hat[0][:, index].reshape([len(grad_u_hat[0]), 1])
        temp = torch.autograd.grad(outputs = p_temp, inputs = x, grad_outputs = torch.ones(p_temp.shape).cuda(), create_graph = True, allow_unused = True)[0]
        laplace_u_hat = temp[:, index].reshape([len(grad_u_hat[0]), 1]) + laplace_u_hat
    index_t = d - 1
    u_hat_t = grad_u_hat[0][:, index_t].reshape([len(grad_u_hat[0]), 1])
    part_1 = torch.sum((u_hat_t -laplace_u_hat - f(x))**2) / len(x)
    return part_1


# In[ ]:


optimizer = optim.Adam(net_1.parameters())


# In[ ]:


epoch = 100000
loss_record = np.zeros(epoch)
error_record = np.zeros(epoch)
time_start = time.time()
for i in range(epoch):
    optimizer.zero_grad()
    x = generate_sample(data_size).cuda()
    x.requires_grad = True
    loss = loss_function(x)
    loss_record[i] = float(loss)
    error = relative_l2_error()
    error_record[i] = float(error)
    np.save("DGM_loss_parabolic_10d.npy", loss_record)
    np.save("DGM_error_parabolic_10d.npy", error_record)
    if i % 50 == 0:
        print("current epoch is: ", i)
        print("current loss is: ", loss.detach())
        print("current error is: ", error.detach())
    loss.backward()
    optimizer.step() 
time_end = time.time()
print('total time is: ', time_end-time_start, 'seconds')


# In[ ]:


np.save("DGM_loss_parabolic_10d.npy", loss_record)
np.save("DGM_error_parabolic_10d.npy", error_record)


# In[ ]:




