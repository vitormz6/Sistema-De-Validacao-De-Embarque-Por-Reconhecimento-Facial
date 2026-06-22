import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";

import styles from "./NotFoundPage.module.css";

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className={styles.wrapper}>
      <span className={styles.code}>404</span>
      <p className={styles.message}>Página não encontrada.</p>
      <Button variant="primary" onClick={() => navigate("/dashboard")}>
        Voltar ao dashboard
      </Button>
    </div>
  );
}
