import { httpClient } from "@/api/httpClient";

import type { BoardingValidationResponse } from "@/types";

export const validationApi = {
  async validateBoarding(imageBlob: Blob): Promise<BoardingValidationResponse> {
    const form = new FormData();
    form.append("file", imageBlob, "capture.jpg");
    const response = await httpClient.post<BoardingValidationResponse>(
      "/local/validate-boarding",
      form,
    );
    return response.data;
  },
};
