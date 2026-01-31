import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";
import { Layout } from "@bb/layouts/Layout";
import { Home } from "@bb/pages/home/Home";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MyBacklog } from "@bb/pages/my-backlog/MyBacklog";
import { CreateMyBacklog } from "./pages/create-my-backlog/CreateMyBacklog";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="my-backlog" element={<MyBacklog />} />
            <Route path="create-my-backlog" element={<CreateMyBacklog />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
